import pytest
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.auth import create_access_token
from app.database import engine
from app.deps import get_db
from app.main import app
from app.models import User
from app.ratelimit import review_limiter

TEST_SECRET = "test-secret-key-that-is-long-enough-for-hs256"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    review_limiter.reset()
    yield
    review_limiter.reset()


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


@pytest.fixture()
def secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)


@pytest.fixture()
def make_user(api_db, secret_key):
    def _make(subject="student-1", provider="test", is_active=True):
        user = User(
            display_name="دانش‌آموز آزمایشی",
            auth_provider=provider,
            auth_subject=subject,
            is_active=is_active,
        )
        api_db.add(user)
        api_db.flush()
        token = create_access_token(user.id)
        return user, {"Authorization": f"Bearer {token}"}

    return _make