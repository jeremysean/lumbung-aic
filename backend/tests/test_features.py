from __future__ import annotations

import pandas as pd
import pytest

from app.features import InputValidationError, REQUIRED_COLUMNS, validate_snapshot


def valid_frame() -> pd.DataFrame:
    rows = []
    for day in range(28):
        rows.append(
            {
                "date": f"2026-01-{day + 1:02d}",
                "sku_id": "SKU-001",
                "category": "Makanan",
                "sales_qty": day % 3,
                "stock_on_hand": 20,
                "on_order": 0,
                "unit_cost": 2_000,
                "unit_margin": 500,
                "lead_time_days": 4,
                "moq": 6,
                "available_budget": 100_000,
            }
        )
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)


def test_valid_snapshot_passes():
    assert len(validate_snapshot(valid_frame())) == 28


def test_missing_column_is_rejected():
    with pytest.raises(InputValidationError, match="Skema CSV"):
        validate_snapshot(valid_frame().drop(columns=["moq"]))


def test_missing_value_is_rejected():
    frame = valid_frame()
    frame.loc[0, "unit_cost"] = None
    with pytest.raises(InputValidationError, match="tidak valid"):
        validate_snapshot(frame)


def test_budget_must_be_store_level_constant():
    frame = valid_frame()
    frame.loc[0, "available_budget"] = 50_000
    with pytest.raises(InputValidationError, match="tidak valid"):
        validate_snapshot(frame)

