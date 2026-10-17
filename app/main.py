import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import cors_origins, frontend_dir
from app.database import engine
from app.errors import (
    ApiError,
    api_error_handler,
    error_response,
    http_error_handler,
    validation_error_handler,
)
from app.frontend import mount_frontend
from app.logging_config import setup_logging
from app.routers import (
    admin_catalog,
    admin_reviews,
    auth,
    compare,
    reviews,
    rivals,
    subjects,
    teachers,
)

setup_logging()
logger = logging.getLogger("baf.request")

ROUTERS = [
    subjects,
    teachers,
    reviews,
    rivals,
    compare,
    auth,
    admin_reviews,
    admin_catalog,
]

MAX_BODY_BYTES = 64 * 1024

app = FastAPI(title="Baf API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return error_response(
            413, "PAYLOAD_TOO_LARGE", "حجم درخواست بیش از حد مجاز است."
        )
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/api/v1/admin") or request.url.path.startswith(
        "/api/v1/auth"
    ):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.middleware("http")
async def request_logging(request: Request, call_next):
    """بیرونی‌ترین لایه: هر درخواست شناسه می‌گیرد. بدنه و query هرگز لاگ نمی‌شوند."""
    request_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_id=%s %s %s unhandled error",
            request_id,
            request.method,
            request.url.path,
        )
        return error_response(
            500,
            "INTERNAL_ERROR",
            "خطای داخلی سرور.",
            headers={"X-Request-ID": request_id},
        )
    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s %s %s -> %s %.0fms",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)

for module in ROUTERS:
    app.include_router(module.router, prefix="/api/v1")


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}


# باید آخرین مورد باشد: همه‌ی مسیرهای دیگر را (غیر از API) به فرانت می‌دهد
mount_frontend(app, frontend_dir())