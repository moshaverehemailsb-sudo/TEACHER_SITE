import os

import pytest
from dotenv import load_dotenv

load_dotenv()

_main_url = os.getenv("DATABASE_URL", "").strip()
_test_url = os.getenv("TEST_DATABASE_URL", "").strip()
if not _test_url:
    pytest.exit(
        "TEST_DATABASE_URL is not set. Tests must run on a separate test database.",
        returncode=2,
    )
if _test_url == _main_url:
    pytest.exit("TEST_DATABASE_URL must differ from DATABASE_URL.", returncode=2)
os.environ["DATABASE_URL"] = _test_url

from sqlalchemy.orm import Session  # noqa: E402

import app.models  # noqa: E402,F401
from app.auth import create_access_token  # noqa: E402
from app.database import engine  # noqa: E402
from app.deps import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.ratelimit import ALL_LIMITERS  # noqa: E402

TEST_SECRET = "test-secret-key-that-is-long-enough-for-hs256"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    for limiter in ALL_LIMITERS:
        limiter.reset()
    yield
    for limiter in ALL_LIMITERS:
        limiter.reset()


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