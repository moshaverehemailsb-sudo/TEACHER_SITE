import pytest
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.database import engine
from app.deps import get_db
from app.main import app


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def api_db(db):
    """درخواست‌های API را از همان نشست برگشت‌پذیر تست عبور می‌دهد."""
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_headers(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
    return {"Authorization": "Bearer test-token"}