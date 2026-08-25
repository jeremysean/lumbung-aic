import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_health_exposes_model_version():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["model_version"]


def test_recommendation_contract():
    sample = ROOT / "data" / "sample_store_snapshot.csv"
    with sample.open("rb") as handle:
        response = client.post("/v1/recommendations", files={"file": (sample.name, handle, "text/csv")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposed_spend"] <= payload["data"]["budget"]
    assert payload["meta"]["trace_id"] == response.headers["X-Trace-Id"]


def test_non_csv_rejected_with_problem_details():
    response = client.post("/v1/recommendations", files={"file": ("bad.txt", b"bad", "text/plain")})
    assert response.status_code == 415
    assert response.json()["code"] == "UNSUPPORTED_FILE"


def test_exported_openapi_contract_matches_application():
    exported = json.loads((ROOT / "docs" / "openapi.json").read_text(encoding="utf-8"))
    assert exported == app.openapi()
    recommendation = exported["paths"]["/v1/recommendations"]["post"]
    assert recommendation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/RecommendationEnvelope"
    )
    assert recommendation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ProblemDetails"
    )
