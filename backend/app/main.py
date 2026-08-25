from __future__ import annotations

import io
import logging
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

from .features import InputValidationError, read_snapshot
from .service import load_bundle, recommend

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("lumbung")

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", ROOT / "artifacts"))
SAMPLE_PATH = Path(os.getenv("SAMPLE_PATH", ROOT / "data" / "sample_store_snapshot.csv"))
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Lumbung Replenishment API",
    version="1.0.0",
    description="Budget-aware probabilistic replenishment for independent retailers.",
)


def problem(status: int, code: str, message: str, trace_id: str, details: list | None = None):
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://lumbung.local/problems/{code.lower()}",
            "title": message,
            "status": status,
            "code": code,
            "trace_id": trace_id,
            "details": details or [],
        },
    )


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(InputValidationError)
async def input_error_handler(request: Request, exc: InputValidationError):
    return problem(422, "INVALID_SNAPSHOT", str(exc), request.state.trace_id, exc.details)


@app.exception_handler(RequestValidationError)
async def request_error_handler(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(map(str, error["loc"])), "issue": error["msg"]} for error in exc.errors()]
    return problem(422, "INVALID_REQUEST", "Permintaan tidak valid.", request.state.trace_id, details)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error trace_id=%s", request.state.trace_id)
    return problem(500, "INTERNAL_ERROR", "Inference gagal diproses.", request.state.trace_id)


@app.get("/health", tags=["system"])
def health():
    bundle = load_bundle(ARTIFACT_DIR)
    return {"data": {"status": "ok", "model_version": bundle.metadata["model_version"]}}


@app.get("/v1/templates/store-snapshot", tags=["recommendations"])
def download_template():
    if not SAMPLE_PATH.exists():
        return problem(404, "SAMPLE_NOT_FOUND", "Contoh CSV tidak tersedia.", str(uuid.uuid4()))
    return StreamingResponse(
        io.BytesIO(SAMPLE_PATH.read_bytes()),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_store_snapshot.csv"'},
    )


@app.post("/v1/recommendations", tags=["recommendations"])
async def create_recommendation(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        return problem(415, "UNSUPPORTED_FILE", "Unggah file dengan format .csv.", request.state.trace_id)
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return problem(413, "FILE_TOO_LARGE", "Ukuran file maksimal 10 MB.", request.state.trace_id)
    frame = read_snapshot(io.BytesIO(raw))
    bundle = load_bundle(ARTIFACT_DIR)
    result = recommend(frame, bundle)
    return {"data": result, "meta": {"trace_id": request.state.trace_id}}

