from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.features import read_snapshot  # noqa: E402
from app.service import load_bundle, recommend  # noqa: E402

CONVENTIONAL_COMMIT = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?!?: .+"
)
REQUIRED_FILES = (
    "README.md",
    "MODEL_CARD.md",
    "SUBMISSION_CHECKLIST.md",
    "docs/CLAIMS_REGISTER.md",
    "docs/VIDEO_RUNBOOK.md",
    "docs/openapi.json",
    "docker-compose.yml",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "data/sample_store_snapshot.csv",
    "data/synthetic_training_history.csv",
    "artifacts/replenishment_models.joblib",
    "artifacts/model_metadata.json",
)


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    failures: list[str] = []
    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            failures.append(f"required file missing: {relative_path}")

    metadata_path = ROOT / "artifacts" / "model_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    training_path = ROOT / "data" / "synthetic_training_history.csv"
    actual_hash = hashlib.sha256(training_path.read_bytes()).hexdigest()
    if actual_hash != metadata.get("data_sha256"):
        failures.append("training data SHA-256 does not match model metadata")
    if metadata.get("acceptance_gate_passed") is not True:
        failures.append("model acceptance gate is not recorded as passed")

    subjects = git_output("log", "--format=%s").splitlines()
    invalid_subjects = [subject for subject in subjects if not CONVENTIONAL_COMMIT.fullmatch(subject)]
    if invalid_subjects:
        failures.append(f"non-Conventional Commit subjects: {invalid_subjects}")

    sample = read_snapshot(ROOT / "data" / "sample_store_snapshot.csv")
    bundle = load_bundle(ROOT / "artifacts")
    first = recommend(sample, bundle)
    second = recommend(sample, bundle)
    if first != second:
        failures.append("sample inference is not deterministic")
    if first["proposed_spend"] > first["budget"]:
        failures.append("sample recommendation exceeds budget")
    invalid_moq = [
        item["sku_id"]
        for item in first["items"]
        if item["order_qty"] % item["moq"] != 0
    ]
    if invalid_moq:
        failures.append(f"sample recommendation violates MOQ: {invalid_moq}")

    report = {
        "status": "failed" if failures else "passed",
        "required_files": len(REQUIRED_FILES),
        "commits_checked": len(subjects),
        "model_version": metadata["model_version"],
        "acceptance_gate_passed": metadata["acceptance_gate_passed"],
        "sample_items": len(first["items"]),
        "sample_budget": first["budget"],
        "sample_proposed_spend": first["proposed_spend"],
        "git_remotes": git_output("remote").splitlines(),
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
