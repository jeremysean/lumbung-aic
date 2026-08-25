from pathlib import Path

from app.features import read_snapshot
from app.service import load_bundle, recommend

ROOT = Path(__file__).resolve().parents[2]


def test_inference_is_deterministic_and_feasible():
    frame = read_snapshot(ROOT / "data" / "sample_store_snapshot.csv")
    bundle = load_bundle(ROOT / "artifacts")
    first = recommend(frame, bundle)
    second = recommend(frame, bundle)
    assert first == second
    assert first["proposed_spend"] <= first["budget"]
    assert all(item["order_qty"] % item["moq"] == 0 for item in first["items"])

