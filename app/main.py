from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import cors_origins
from app.database import engine
from app.errors import (
    ApiError,
    api_error_handler,
    error_response,
    http_error_handler,
    validation_error_handler,
)
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