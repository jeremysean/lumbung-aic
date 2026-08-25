from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
from lightgbm import LGBMRegressor
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_pinball_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.features import FEATURE_COLUMNS, build_supervised_examples, read_snapshot  # noqa: E402


PARAMETER_GRID = (
    {"n_estimators": 220, "learning_rate": 0.035, "num_leaves": 15, "max_depth": 5, "min_child_samples": 20},
    {"n_estimators": 300, "learning_rate": 0.025, "num_leaves": 23, "max_depth": 6, "min_child_samples": 16},
    {"n_estimators": 180, "learning_rate": 0.05, "num_leaves": 15, "max_depth": 5, "min_child_samples": 24},
)


def make_model(alpha: float, params: dict) -> Pipeline:
    preprocess = ColumnTransformer(
        [("category", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), ["category"])],
        remainder="passthrough",
        verbose_feature_names_out=False,
    )
    preprocess.set_output(transform="pandas")
    regressor = LGBMRegressor(
        objective="quantile",
        alpha=alpha,
        random_state=20260825,
        deterministic=True,
        force_col_wise=True,
        verbosity=-1,
        reg_alpha=0.05,
        reg_lambda=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        **params,
    )
    return Pipeline([("preprocess", preprocess), ("regressor", regressor)])


def temporal_partitions(examples: pd.DataFrame):
    dates = np.sort(examples["target_end_date"].unique())
    fold_1 = pd.Timestamp(dates[int(len(dates) * 0.62)])
    fold_2 = pd.Timestamp(dates[int(len(dates) * 0.76)])
    test_start = pd.Timestamp(dates[int(len(dates) * 0.88)])
    return fold_1, fold_2, test_start


def tune(examples: pd.DataFrame, fold_1: pd.Timestamp, fold_2: pd.Timestamp) -> tuple[dict, list[dict]]:
    folds = (
        (examples["target_end_date"] <= fold_1, (examples["cutoff_date"] > fold_1) & (examples["target_end_date"] <= fold_2)),
        (examples["target_end_date"] <= fold_2, (examples["cutoff_date"] > fold_2)),
    )
    results: list[dict] = []
    for params in PARAMETER_GRID:
        scores = []
        for train_mask, validation_mask in folds:
            train = examples.loc[train_mask]
            validation = examples.loc[validation_mask]
            fold_score = 0.0
            for alpha in (0.5, 0.9):
                model = make_model(alpha, params)
                model.fit(train[FEATURE_COLUMNS], train["target"])
                prediction = np.maximum(0.0, model.predict(validation[FEATURE_COLUMNS]))
                fold_score += mean_pinball_loss(validation["target"], prediction, alpha=alpha)
            scores.append(fold_score / 2)
        results.append(
            {
                "params": params,
                "mean_pinball_loss": round(float(np.mean(scores)), 6),
                "std_pinball_loss": round(float(np.std(scores)), 6),
                "fold_scores": [round(float(score), 6) for score in scores],
            }
        )
    best = min(results, key=lambda item: (item["mean_pinball_loss"], item["std_pinball_loss"]))
    return best["params"], results


def evaluate(test: pd.DataFrame, p50_model: Pipeline, p90_model: Pipeline, p90_offset: float) -> dict:
    target = test["target"].to_numpy()
    p50 = np.maximum(0.0, p50_model.predict(test[FEATURE_COLUMNS]))
    p90 = np.maximum(p50, p90_model.predict(test[FEATURE_COLUMNS]) + p90_offset)
    baseline_p50 = np.maximum(0.0, test["rolling_mean_28"].to_numpy() * test["horizon_days"].to_numpy())
    baseline_p90 = np.maximum(
        baseline_p50,
        baseline_p50 + 1.2816 * test["rolling_std_28"].to_numpy() * np.sqrt(test["horizon_days"].to_numpy()),
    )
    denominator = max(float(np.abs(target).sum()), 1.0)
    return {
        "test_examples": int(len(test)),
        "p50_pinball_loss": round(float(mean_pinball_loss(target, p50, alpha=0.5)), 6),
        "p90_pinball_loss": round(float(mean_pinball_loss(target, p90, alpha=0.9)), 6),
        "mean_pinball_loss": round(
            float((mean_pinball_loss(target, p50, alpha=0.5) + mean_pinball_loss(target, p90, alpha=0.9)) / 2), 6
        ),
        "baseline_mean_pinball_loss": round(
            float(
                (mean_pinball_loss(target, baseline_p50, alpha=0.5) + mean_pinball_loss(target, baseline_p90, alpha=0.9))
                / 2
            ),
            6,
        ),
        "wape_p50": round(float(np.abs(target - p50).sum() / denominator), 6),
        "baseline_wape": round(float(np.abs(target - baseline_p50).sum() / denominator), 6),
        "p90_coverage": round(float(np.mean(target <= p90)), 6),
        "mean_forecast_bias_p50": round(float(np.mean(p50 - target)), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune and train Lumbung quantile models.")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "synthetic_training_history.csv")
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()

    raw_bytes = args.data.read_bytes()
    frame = read_snapshot(args.data)
    examples = build_supervised_examples(frame)
    fold_1, fold_2, test_start = temporal_partitions(examples)
    tuning_pool = examples.loc[examples["target_end_date"] < test_start].copy()
    best_params, tuning_results = tune(tuning_pool, fold_1, fold_2)

    train = examples.loc[examples["target_end_date"] < test_start]
    test = examples.loc[examples["cutoff_date"] >= test_start]
    calibration_train = examples.loc[examples["target_end_date"] <= fold_2]
    calibration = examples.loc[
        (examples["cutoff_date"] > fold_2) & (examples["target_end_date"] < test_start)
    ]
    calibration_model = make_model(0.9, best_params).fit(
        calibration_train[FEATURE_COLUMNS], calibration_train["target"]
    )
    calibration_residuals = calibration["target"].to_numpy() - calibration_model.predict(
        calibration[FEATURE_COLUMNS]
    )
    p90_offset = max(0.0, float(np.quantile(calibration_residuals, 0.9)))
    p50_model = make_model(0.5, best_params).fit(train[FEATURE_COLUMNS], train["target"])
    p90_model = make_model(0.9, best_params).fit(train[FEATURE_COLUMNS], train["target"])
    metrics = evaluate(test, p50_model, p90_model, p90_offset)

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"p50": p50_model, "p90": p90_model}, args.artifact_dir / "replenishment_models.joblib")
    metadata = {
        "model_version": "lumbung-lightgbm-quantile-1.0.0",
        "parameter_version": "replenishment-v1",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_source": "Reproducible synthetic retail history; not field evidence.",
        "data_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "data_cutoff": str(frame["date"].max().date()),
        "random_seed": 20260825,
        "feature_columns": FEATURE_COLUMNS,
        "validation": {
            "strategy": "two expanding-window tuning folds plus untouched temporal test",
            "test_start": str(test_start.date()),
            "tuning_results": tuning_results,
        },
        "best_parameters": best_params,
        "p90_calibration_offset": round(p90_offset, 6),
        "metrics": metrics,
        "acceptance_gate_passed": bool(
            metrics["mean_pinball_loss"] < metrics["baseline_mean_pinball_loss"]
            and metrics["wape_p50"] <= metrics["baseline_wape"]
        ),
        "limitations": [
            "Synthetic demand is used for software verification and cannot establish field impact.",
            "Zero sales may represent stockout-censored demand in real POS data.",
            "The model must be revalidated and retrained before use on a new retail population.",
        ],
    }
    (args.artifact_dir / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"best_parameters": best_params, "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
