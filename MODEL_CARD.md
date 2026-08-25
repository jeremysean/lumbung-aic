# Model Card: Lumbung Quantile Replenishment v1

## Intended use

The model estimates P50 and P90 aggregate SKU demand over a purchase horizon of supplier lead time plus a fixed seven-day review period. Its output feeds a deterministic replenishment and budget-allocation layer. It is decision support for a store owner, not an autonomous purchasing system.

## Model and fine-tuning

- Learner: two LightGBM gradient-boosted tree regressors with quantile objectives at 0.5 and 0.9.
- Model version: `lumbung-lightgbm-quantile-1.0.0`.
- Parameter version: `replenishment-v1`.
- Seed: `20260825`.
- Search: three documented parameter candidates over two expanding temporal validation folds.
- Selected parameters: 220 trees, learning rate 0.035, 15 leaves, maximum depth 5, and 20 minimum child samples.
- Calibration: additive P90 offset selected from residuals on a pre-test chronological calibration window.

Features are category, demand lags, shifted rolling demand summaries, zero rate, explicit leakage-safe baseline forecasts, calendar values, cost, margin, lead time, requested horizon, and available history length. Future sales do not enter features.

## Data

The artifact is trained on 3,520 rows covering 16 reproducibly generated synthetic SKU series over 220 days. Synthetic data is permitted for the competition prototype but cannot support field-impact claims. The full generator is `scripts/generate_demo_data.py`; the exact raw SHA-256 is stored in `artifacts/model_metadata.json`.

## Evaluation

Validation is chronological. Hyperparameters use two expanding windows; the final test starts later and is touched only after selection. The untouched test contains 432 SKU-horizon examples.

| Metric | Result |
|---|---:|
| P50 pinball loss | 2.243350 |
| P90 pinball loss | 1.329433 |
| Mean pinball loss | 1.786392 |
| Moving-average baseline mean pinball loss | 1.828699 |
| P50 WAPE | 0.200564 |
| Moving-average baseline WAPE | 0.205738 |
| P90 empirical coverage | 0.891204 |
| Mean P50 forecast bias | -1.262518 units |

The predeclared gate passes because both mean pinball loss and WAPE improve over the baseline. The gain is small and must not be generalized beyond this synthetic test.

## Decision safeguards

- Negative forecasts are clipped to zero.
- P90 cannot be lower than P50.
- Stock on hand and on-order units reduce the raw requirement.
- Quantities are rounded to complete MOQ bundles.
- A bounded-knapsack optimizer cannot exceed the provided budget.
- Identical normalized input and model versions produce identical output.
- Every response contains model version, cutoff, input checksum, and fixed review period.

## Limitations and prohibited claims

- Real zero sales can mean no demand or an unobserved stockout.
- Synthetic promotion, trend, and intermittency patterns may not match an Indonesian retailer.
- No causal impact on stockout, fill rate, revenue, waste, or cash flow has been measured.
- No claim of savings, adoption, willingness to pay, or regulatory compliance is supported.
- Retraining, calibration, stock-accuracy checks, and a prospective pilot are required before operational use.

