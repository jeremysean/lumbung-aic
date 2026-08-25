from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CATEGORIES = ("Makanan", "Minuman", "Kebutuhan Rumah", "Perawatan")


def generate_store(seed: int, sku_count: int, days: int, budget: float) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-01-01")
    records: list[dict] = []
    for sku_index in range(sku_count):
        sku_id = f"SKU-{sku_index + 1:03d}"
        category = CATEGORIES[sku_index % len(CATEGORIES)]
        base = 0.45 + (sku_index % 6) * 0.55
        intermittent = sku_index % 5 == 4
        unit_cost = float(2_500 + (sku_index % 8) * 2_250)
        unit_margin = round(unit_cost * (0.12 + (sku_index % 4) * 0.035), 2)
        lead_time = int(3 + (sku_index % 5) * 2)
        moq = int((1, 6, 12, 24)[sku_index % 4])
        stock = int(25 + rng.integers(0, 30))
        for day_index in range(days):
            date = start + pd.Timedelta(days=day_index)
            weekly = 1.0 + (0.35 if date.dayofweek in (5, 6) else -0.08)
            trend = 1.0 + 0.0018 * day_index
            promo = 1.65 if (day_index + sku_index * 3) % 41 in (0, 1, 2) else 1.0
            demand_rate = base * weekly * trend * promo
            if intermittent and rng.random() < 0.62:
                sales = 0
            else:
                sales = int(rng.poisson(demand_rate))
            stock = max(0, stock - sales)
            if day_index % (lead_time + 7) == 0:
                stock += int(max(moq, np.ceil(base * 18 / moq) * moq))
            records.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "sku_id": sku_id,
                    "category": category,
                    "sales_qty": sales,
                    "stock_on_hand": stock,
                    "on_order": 0,
                    "unit_cost": unit_cost,
                    "unit_margin": unit_margin,
                    "lead_time_days": lead_time,
                    "moq": moq,
                    "available_budget": budget,
                }
            )
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reproducible synthetic Lumbung data.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    training = generate_store(seed=20260825, sku_count=16, days=220, budget=8_000_000)
    training.to_csv(args.output_dir / "synthetic_training_history.csv", index=False)

    sample = generate_store(seed=18082026, sku_count=8, days=100, budget=2_500_000)
    # Make the current snapshot decision non-trivial without altering historical demand.
    latest_date = sample["date"].max()
    latest_mask = sample["date"] == latest_date
    sample.loc[latest_mask, "stock_on_hand"] = [1, 3, 0, 5, 2, 8, 1, 4]
    sample.to_csv(args.output_dir / "sample_store_snapshot.csv", index=False)
    print(f"Generated {len(training):,} training rows and {len(sample):,} sample rows.")


if __name__ == "__main__":
    main()

