from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.database import engine
from app.errors import ApiError, api_error_handler
from app.routers import compare, reviews, rivals, subjects, teachers

app = FastAPI(title="Baf API", version="0.1.0")

app.add_exception_handler(ApiError, api_error_handler)
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(rivals.router, prefix="/api/v1")
app.include_router(compare.router, prefix="/api/v1")


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}