from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import ceil
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .features import FEATURE_COLUMNS, prepare_inference
from .optimizer import Candidate, allocate_budget


@dataclass
class ModelBundle:
    p50_model: object
    p90_model: object
    metadata: dict


def load_bundle(artifact_dir: Path) -> ModelBundle:
    model_path = artifact_dir / "replenishment_models.joblib"
    metadata_path = artifact_dir / "model_metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise RuntimeError("Model artifacts missing. Run `python scripts/train_model.py` first.")
    models = joblib.load(model_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return ModelBundle(models["p50"], models["p90"], metadata)


def _reason(row: pd.Series) -> str:
    if row["order_qty"] > 0:
        if row["stock_on_hand"] < row["forecast_p50"]:
            return "Stok tidak menutup kebutuhan median hingga pemasok datang."
        return "Risiko stockout P90 tinggi dan nilai perlindungan per rupiah kompetitif."
    if row["recommended_qty"] <= 0:
        return "Stok dan barang dalam perjalanan masih menutup kebutuhan P90."
    return "Kebutuhan terdeteksi, tetapi kalah prioritas dalam batas anggaran."


def recommend(frame: pd.DataFrame, bundle: ModelBundle, review_period_days: int = 7) -> dict:
    prepared = prepare_inference(frame, review_period_days)
    feature_frame = prepared.inference_rows[FEATURE_COLUMNS]
    p50 = np.maximum(0.0, bundle.p50_model.predict(feature_frame))
    p90_offset = float(bundle.metadata.get("p90_calibration_offset", 0.0))
    p90 = np.maximum(p50, bundle.p90_model.predict(feature_frame) + p90_offset)

    result = prepared.latest.merge(
        prepared.inference_rows[["sku_id", "horizon_days", "rolling_mean_28"]], on="sku_id"
    )
    result["forecast_p50"] = np.round(p50, 2)
    result["forecast_p90"] = np.round(p90, 2)
    result["target_stock"] = np.ceil(result["forecast_p90"]).astype(int)
    result["shortage_units"] = np.maximum(
        0.0, result["forecast_p90"] - result["stock_on_hand"] - result["on_order"]
    )
    result["recommended_qty"] = result.apply(
        lambda row: int(ceil(row["shortage_units"] / row["moq"]) * row["moq"])
        if row["shortage_units"] > 0
        else 0,
        axis=1,
    )
    result["stockout_risk"] = np.where(
        result["forecast_p90"] > 0,
        np.clip(result["shortage_units"] / result["forecast_p90"], 0.0, 1.0),
        0.0,
    )

    candidates = [
        Candidate(
            sku_id=str(row.sku_id),
            moq=int(row.moq),
            max_units=int(row.recommended_qty),
            unit_cost=float(row.unit_cost),
            unit_margin=float(row.unit_margin),
            shortage_units=float(row.shortage_units),
            stockout_risk=float(row.stockout_risk),
        )
        for row in result.itertuples()
        if row.recommended_qty > 0
    ]
    allocation = allocate_budget(candidates, prepared.budget)
    result["order_qty"] = result["sku_id"].map(allocation).fillna(0).astype(int)
    result["order_cost"] = (result["order_qty"] * result["unit_cost"]).round(2)
    result["decision"] = np.where(result["order_qty"] > 0, "BELI_SEKARANG", "TUNDA")
    result["reason"] = result.apply(_reason, axis=1)
    result["priority_score"] = (
        result["stockout_risk"] * result["unit_margin"] / result["unit_cost"].clip(lower=0.01)
    ).round(6)

    output_columns = [
        "sku_id",
        "category",
        "decision",
        "order_qty",
        "moq",
        "unit_cost",
        "order_cost",
        "stock_on_hand",
        "on_order",
        "horizon_days",
        "forecast_p50",
        "forecast_p90",
        "stockout_risk",
        "priority_score",
        "reason",
    ]
    result = result[output_columns].sort_values(
        ["decision", "priority_score", "sku_id"], ascending=[True, False, True]
    )
    input_checksum = hashlib.sha256(
        frame.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")
    ).hexdigest()
    records = result.to_dict(orient="records")
    for record in records:
        for key, value in record.items():
            if isinstance(value, (np.integer,)):
                record[key] = int(value)
            elif isinstance(value, (np.floating,)):
                record[key] = float(value)
    return {
        "budget": round(prepared.budget, 2),
        "proposed_spend": round(float(result["order_cost"].sum()), 2),
        "budget_utilization": round(float(result["order_cost"].sum() / prepared.budget), 4),
        "items": records,
        "audit": {
            "model_version": bundle.metadata["model_version"],
            "parameter_version": bundle.metadata["parameter_version"],
            "data_cutoff": bundle.metadata["data_cutoff"],
            "input_sha256": input_checksum,
            "review_period_days": review_period_days,
        },
    }
