from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "date",
    "sku_id",
    "category",
    "sales_qty",
    "stock_on_hand",
    "on_order",
    "unit_cost",
    "unit_margin",
    "lead_time_days",
    "moq",
    "available_budget",
]

NUMERIC_COLUMNS = [
    "sales_qty",
    "stock_on_hand",
    "on_order",
    "unit_cost",
    "unit_margin",
    "lead_time_days",
    "moq",
    "available_budget",
]

FEATURE_COLUMNS = [
    "category",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_28",
    "rolling_std_28",
    "zero_rate_28",
    "recent_sum_7",
    "recent_sum_28",
    "moving_average_forecast",
    "seasonal_naive_forecast",
    "dispersion_horizon",
    "day_of_week",
    "month",
    "unit_cost",
    "unit_margin",
    "lead_time_days",
    "horizon_days",
    "history_days",
]


class InputValidationError(ValueError):
    def __init__(self, message: str, details: list[dict[str, str]] | None = None):
        super().__init__(message)
        self.details = details or []


@dataclass(frozen=True)
class PreparedInput:
    history: pd.DataFrame
    inference_rows: pd.DataFrame
    latest: pd.DataFrame
    budget: float


def read_snapshot(source: str | Path | object) -> pd.DataFrame:
    try:
        frame = pd.read_csv(source)
    except Exception as exc:
        raise InputValidationError(
            "File tidak dapat dibaca sebagai CSV.",
            [{"field": "file", "issue": str(exc)}],
        ) from exc
    return validate_snapshot(frame)


def validate_snapshot(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise InputValidationError(
            "Skema CSV belum lengkap.",
            [{"field": column, "issue": "kolom wajib tidak ditemukan"} for column in missing],
        )
    frame = frame[REQUIRED_COLUMNS].copy()
    if frame.empty:
        raise InputValidationError("CSV tidak berisi data.")

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    details: list[dict[str, str]] = []
    for column in REQUIRED_COLUMNS:
        count = int(frame[column].isna().sum())
        if count:
            details.append({"field": column, "issue": f"{count} nilai kosong atau tidak valid"})
    for column in NUMERIC_COLUMNS:
        count = int((frame[column] < 0).sum())
        if count:
            details.append({"field": column, "issue": f"{count} nilai negatif tidak diizinkan"})
    if (frame["moq"] < 1).any():
        details.append({"field": "moq", "issue": "MOQ harus minimal 1"})
    if ((frame["moq"] % 1) != 0).any():
        details.append({"field": "moq", "issue": "MOQ harus berupa unit bulat"})
    if (frame["lead_time_days"] < 1).any():
        details.append({"field": "lead_time_days", "issue": "lead time harus minimal 1 hari"})
    if ((frame["lead_time_days"] % 1) != 0).any():
        details.append({"field": "lead_time_days", "issue": "lead time harus berupa hari bulat"})
    if (frame["sku_id"].astype(str).str.strip() == "").any():
        details.append({"field": "sku_id", "issue": "SKU tidak boleh kosong"})
    if frame.duplicated(["sku_id", "date"]).any():
        details.append({"field": "date", "issue": "tanggal per SKU harus unik"})

    budgets = frame["available_budget"].dropna().round(2).unique()
    if len(budgets) != 1:
        details.append(
            {"field": "available_budget", "issue": "gunakan satu nilai anggaran yang sama di semua baris"}
        )
    elif budgets[0] <= 0:
        details.append({"field": "available_budget", "issue": "anggaran harus lebih dari nol"})

    if details:
        raise InputValidationError("Data CSV tidak valid.", details)

    frame["sku_id"] = frame["sku_id"].astype(str).str.strip()
    frame["category"] = frame["category"].astype(str).str.strip()
    counts = frame.groupby("sku_id")["date"].nunique()
    short = counts[counts < 28]
    if not short.empty:
        raise InputValidationError(
            "Setiap SKU memerlukan minimal 28 hari histori.",
            [{"field": sku, "issue": f"hanya {days} hari"} for sku, days in short.items()],
        )
    return frame.sort_values(["sku_id", "date"]).reset_index(drop=True)


def _series_features(history: pd.DataFrame, cutoff: pd.Timestamp, horizon_days: int) -> dict[str, float | str]:
    past = history.loc[history["date"] <= cutoff].sort_values("date")
    sales = past.set_index("date")["sales_qty"].asfreq("D", fill_value=0.0)
    latest = past.iloc[-1]

    def lag(days: int) -> float:
        return float(sales.iloc[-days]) if len(sales) >= days else 0.0

    window_7 = sales.tail(7)
    window_28 = sales.tail(28)
    recent_sum_7 = float(window_7.sum())
    recent_sum_28 = float(window_28.sum())
    return {
        "category": str(latest["category"]),
        "lag_1": lag(1),
        "lag_7": lag(7),
        "lag_14": lag(14),
        "rolling_mean_7": float(window_7.mean()),
        "rolling_mean_28": float(window_28.mean()),
        "rolling_std_28": float(window_28.std(ddof=0)),
        "zero_rate_28": float((window_28 == 0).mean()),
        "recent_sum_7": recent_sum_7,
        "recent_sum_28": recent_sum_28,
        "moving_average_forecast": float(window_28.mean() * horizon_days),
        "seasonal_naive_forecast": float(recent_sum_7 * horizon_days / 7),
        "dispersion_horizon": float(window_28.std(ddof=0) * np.sqrt(horizon_days)),
        "day_of_week": int(cutoff.dayofweek),
        "month": int(cutoff.month),
        "unit_cost": float(latest["unit_cost"]),
        "unit_margin": float(latest["unit_margin"]),
        "lead_time_days": int(latest["lead_time_days"]),
        "horizon_days": int(horizon_days),
        "history_days": int(len(sales)),
    }


def prepare_inference(frame: pd.DataFrame, review_period_days: int = 7) -> PreparedInput:
    records: list[dict[str, float | str]] = []
    latest_rows: list[pd.Series] = []
    for sku_id, group in frame.groupby("sku_id", sort=True):
        latest = group.sort_values("date").iloc[-1].copy()
        latest["sku_id"] = sku_id
        horizon = int(latest["lead_time_days"]) + review_period_days
        feature = _series_features(group, pd.Timestamp(latest["date"]), horizon)
        feature["sku_id"] = sku_id
        records.append(feature)
        latest_rows.append(latest)
    return PreparedInput(
        history=frame,
        inference_rows=pd.DataFrame(records),
        latest=pd.DataFrame(latest_rows).reset_index(drop=True),
        budget=float(frame["available_budget"].iloc[0]),
    )


def build_supervised_examples(frame: pd.DataFrame, horizons: tuple[int, ...] = (7, 14, 21)) -> pd.DataFrame:
    examples: list[dict[str, float | str | pd.Timestamp]] = []
    for sku_id, group in frame.groupby("sku_id", sort=True):
        group = group.sort_values("date").reset_index(drop=True)
        sales_by_date = group.set_index("date")["sales_qty"].asfreq("D", fill_value=0.0)
        dates = sales_by_date.index
        for position in range(27, len(dates) - min(horizons)):
            cutoff = dates[position]
            for horizon in horizons:
                if position + horizon >= len(dates):
                    continue
                target = float(sales_by_date.iloc[position + 1 : position + horizon + 1].sum())
                record = _series_features(group, cutoff, horizon)
                record.update(
                    {
                        "sku_id": sku_id,
                        "cutoff_date": cutoff,
                        "target_end_date": cutoff + pd.Timedelta(days=horizon),
                        "target": target,
                    }
                )
                examples.append(record)
    if not examples:
        raise InputValidationError("Histori belum cukup untuk membangun data training.")
    return pd.DataFrame(examples)
