import logging

import pytest
from fastapi.testclient import TestClient

from app.cleanup import delete_old_codes
from app.main import app
from app.models import LoginCode
from app.sms import get_sms_sender
from datetime import datetime, timedelta, timezone

client = TestClient(app)
PHONE = "09127654321"


class FakeSender:
    def __init__(self):
        self.sent = []

    def send_code(self, phone, code):
        self.sent.append((phone, code))


@pytest.fixture()
def sender(api_db, secret_key, monkeypatch):
    monkeypatch.setenv("PHONE_HASH_KEY", "test-phone-hash-key")
    fake = FakeSender()
    app.dependency_overrides[get_sms_sender] = lambda: fake
    return fake


def test_response_has_request_id():
    response = client.get("/api/v1/subjects")
    assert len(response.headers["x-request-id"]) == 12


def test_unhandled_error_returns_error_format():
    def boom():
        raise RuntimeError("boom")

    app.add_api_route("/__boom__", boom)
    try:
        response = TestClient(app).get("/__boom__")
    finally:
        app.router.routes.pop()
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "x-request-id" in response.headers


def test_logs_do_not_contain_phone_or_code(sender, caplog):
    with caplog.at_level(logging.INFO, logger="baf.request"):
        client.post("/api/v1/auth/request-code", json={"phone": PHONE})
        code = sender.sent[-1][1]
        client.post("/api/v1/auth/verify-code", json={"phone": PHONE, "code": code})
    assert "request-code" in caplog.text
    assert PHONE not in caplog.text
    assert code not in caplog.text


def test_console_sms_requires_development_env(api_db, secret_key, monkeypatch):
    monkeypatch.setenv("PHONE_HASH_KEY", "k")
    monkeypatch.setenv("SMS_PROVIDER", "console")

    monkeypatch.setenv("APP_ENV", "production")
    blocked = client.post("/api/v1/auth/request-code", json={"phone": PHONE})
    assert blocked.status_code == 503
    assert blocked.json()["error"]["code"] == "SMS_DISABLED"

    monkeypatch.setenv("APP_ENV", "development")
    allowed = client.post("/api/v1/auth/request-code", json={"phone": PHONE})
    assert allowed.status_code == 200


def test_cleanup_deletes_only_old_codes(db):
    now = datetime.now(timezone.utc)
    old_a = LoginCode(
        phone_hash="a" * 64,
        code_hash="x" * 64,
        expires_at=now - timedelta(days=2),
        created_at=now - timedelta(days=2),
    )
    old_b = LoginCode(
        phone_hash="b" * 64,
        code_hash="x" * 64,
        expires_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3),
    )
    recent = LoginCode(
        phone_hash="c" * 64,
        code_hash="x" * 64,
        expires_at=now + timedelta(minutes=2),
        created_at=now,
    )
    db.add_all([old_a, old_b, recent])
    db.flush()

    deleted = delete_old_codes(db)
    db.expire_all()

    assert deleted >= 2
    assert db.get(LoginCode, old_a.id) is None
    assert db.get(LoginCode, old_b.id) is None
    assert db.get(LoginCode, recent.id) is not None
    