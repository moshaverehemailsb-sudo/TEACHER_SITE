from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import config
from app.main import app
from app.models import LoginCode
from app.sms import get_sms_sender

client = TestClient(app)


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


def test_config_warnings_report_missing_settings(monkeypatch):
    for name in ("SECRET_KEY", "PHONE_HASH_KEY", "ADMIN_TOKEN", "SMS_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    text = " ".join(config.config_warnings())
    for name in ("SECRET_KEY", "PHONE_HASH_KEY", "ADMIN_TOKEN", "SMS_PROVIDER"):
        assert name in text


def test_config_warnings_are_quiet_with_good_settings(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "s" * 48)
    monkeypatch.setenv("PHONE_HASH_KEY", "p" * 48)
    monkeypatch.setenv("ADMIN_TOKEN", "a" * 48)
    monkeypatch.setenv("SMS_PROVIDER", "some-provider")
    assert config.config_warnings() == []


def test_daily_sms_limit_stops_new_codes(sender, api_db, monkeypatch):
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    current = api_db.scalar(
        select(func.count()).select_from(LoginCode).where(LoginCode.created_at > since)
    )
    monkeypatch.setenv("SMS_DAILY_LIMIT", str(current + 1))

    first = client.post("/api/v1/auth/request-code", json={"phone": "09121110001"})
    assert first.status_code == 200

    second = client.post("/api/v1/auth/request-code", json={"phone": "09121110002"})
    assert second.status_code == 503
    assert second.json()["error"]["code"] == "SMS_LIMIT_REACHED"
    assert len(sender.sent) == 1