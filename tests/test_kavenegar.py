import httpx
import pytest
from fastapi.testclient import TestClient

from app import sms
from app.main import app
from app.sms import KavenegarSender, SmsError, get_sms_sender

client = TestClient(app)
SECRET_KEY_VALUE = "SECRETKEY123"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def test_successful_send_uses_expected_request(monkeypatch):
    calls = []

    def fake_post(url, data=None, timeout=None):
        calls.append((url, data))
        return FakeResponse({"return": {"status": 200, "message": "ok"}})

    monkeypatch.setattr(sms.httpx, "post", fake_post)
    KavenegarSender(SECRET_KEY_VALUE, "2000660110").send_code("09121234567", "482913")
    url, data = calls[0]
    assert url == f"https://api.kavenegar.com/v1/{SECRET_KEY_VALUE}/sms/send.json"
    assert data["receptor"] == "09121234567"
    assert data["sender"] == "2000660110"
    assert "482913" in data["message"]


def test_rejected_request_raises(monkeypatch):
    monkeypatch.setattr(
        sms.httpx, "post", lambda *a, **k: FakeResponse({"return": {"status": 418}})
    )
    with pytest.raises(SmsError):
        KavenegarSender(SECRET_KEY_VALUE, "2000660110").send_code("09121234567", "1")


def test_network_error_does_not_leak_the_api_key(monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.ConnectError(f"cannot reach {args[0]}")

    monkeypatch.setattr(sms.httpx, "post", boom)
    with pytest.raises(SmsError) as info:
        KavenegarSender(SECRET_KEY_VALUE, "2000660110").send_code("09121234567", "1")
    assert SECRET_KEY_VALUE not in str(info.value)
    assert info.value.__cause__ is None


def test_sender_selection(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "kavenegar")
    monkeypatch.setenv("SMS_API_KEY", SECRET_KEY_VALUE)
    monkeypatch.setenv("SMS_SENDER", "2000660110")
    assert isinstance(get_sms_sender(), KavenegarSender)

    monkeypatch.setenv("SMS_API_KEY", "")
    with pytest.raises(Exception) as info:
        get_sms_sender()
    assert getattr(info.value, "code", "") == "SMS_DISABLED"


def test_failed_sms_returns_502_and_does_not_block_retry(api_db, secret_key, monkeypatch):
    monkeypatch.setenv("PHONE_HASH_KEY", "test-phone-hash-key")

    class FailingSender:
        def send_code(self, phone, code):
            raise SmsError("down")

    app.dependency_overrides[get_sms_sender] = lambda: FailingSender()
    for _ in range(2):
        response = client.post("/api/v1/auth/request-code", json={"phone": "09121239999"})
        assert response.status_code == 502
        assert response.json()["error"]["code"] == "SMS_FAILED"