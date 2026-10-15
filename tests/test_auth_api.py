import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.models import User
from app.phone import normalize_phone
from app.sms import get_sms_sender

client = TestClient(app)
AUTH = "/api/v1/auth"
PHONE = "09121234567"


class FakeSender:
    def __init__(self):
        self.sent = []

    def send_code(self, phone, code):
        self.sent.append((phone, code))

    @property
    def last_code(self):
        return self.sent[-1][1]


@pytest.fixture()
def sender(api_db, secret_key, monkeypatch):
    monkeypatch.setenv("PHONE_HASH_KEY", "test-phone-hash-key")
    fake = FakeSender()
    app.dependency_overrides[get_sms_sender] = lambda: fake
    return fake


def request_code(phone=PHONE):
    return client.post(f"{AUTH}/request-code", json={"phone": phone})


def verify(code, phone=PHONE):
    return client.post(f"{AUTH}/verify-code", json={"phone": phone, "code": code})


def wrong_code(real):
    return "000000" if real != "000000" else "111111"


def age_codes(db):
    db.execute(text("UPDATE login_codes SET created_at = now() - interval '5 minutes'"))


def test_normalize_phone_accepts_common_formats():
    for raw in (
        "09121234567",
        "+989121234567",
        "00989121234567",
        "989121234567",
        "9121234567",
        "۰۹۱۲۱۲۳۴۵۶۷",
        "0912 123 4567",
        "0912-123-4567",
    ):
        assert normalize_phone(raw) == PHONE, raw


def test_normalize_phone_rejects_invalid_numbers():
    for raw in ("", "abc", "0812", "09123", "021-1234567", "091212345678"):
        assert normalize_phone(raw) is None, raw


def test_request_code_sends_sms(sender):
    response = request_code()
    assert response.status_code == 200
    data = response.json()
    assert data["retryAfter"] == 60
    assert data["expiresIn"] == 120
    assert len(sender.sent) == 1
    phone, code = sender.sent[0]
    assert phone == PHONE
    assert re.fullmatch(r"\d{6}", code)


def test_request_code_normalizes_phone(sender):
    assert request_code("+98 912 123 4567").status_code == 200
    assert sender.sent[0][0] == PHONE


def test_request_code_rejects_invalid_phone(sender):
    response = request_code("12345")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PHONE"
    assert sender.sent == []


def test_request_code_cannot_be_repeated_immediately(sender):
    assert request_code().status_code == 200
    again = request_code()
    assert again.status_code == 429
    assert again.json()["error"]["code"] == "CODE_RECENTLY_SENT"
    assert len(sender.sent) == 1


def test_verify_code_logs_user_in(sender):
    request_code()
    response = verify(sender.last_code)
    assert response.status_code == 200
    data = response.json()
    assert data["tokenType"] == "bearer"
    assert data["accessToken"]
    assert data["user"]["displayName"]
    me = client.get(
        f"{AUTH}/me", headers={"Authorization": f"Bearer {data['accessToken']}"}
    )
    assert me.json()["id"] == data["user"]["id"]


def test_phone_number_is_not_stored_in_plain_text(sender, api_db):
    request_code()
    user_id = verify(sender.last_code).json()["user"]["id"]
    user = api_db.get(User, user_id)
    assert user.auth_provider == "phone"
    assert PHONE not in user.auth_subject
    assert len(user.auth_subject) == 64


def test_same_phone_logs_into_same_user(sender, api_db):
    request_code()
    first = verify(sender.last_code).json()["user"]["id"]
    age_codes(api_db)
    request_code()
    second = verify(sender.last_code).json()["user"]["id"]
    assert first == second


def test_code_can_only_be_used_once(sender):
    request_code()
    code = sender.last_code
    assert verify(code).status_code == 200
    again = verify(code)
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "CODE_INVALID"


def test_wrong_code_is_rejected_and_attempts_are_limited(sender):
    request_code()
    real = sender.last_code
    for _ in range(5):
        response = verify(wrong_code(real))
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "CODE_INVALID"
    blocked = verify(real)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"


def test_expired_code_is_rejected(sender, api_db):
    request_code()
    api_db.execute(
        text("UPDATE login_codes SET expires_at = now() - interval '1 minute'")
    )
    response = verify(sender.last_code)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CODE_INVALID"


def test_code_of_other_phone_does_not_work(sender):
    request_code()
    response = verify(sender.last_code, phone="09129999999")
    assert response.status_code == 400


def test_persian_digits_in_code_are_accepted(sender):
    request_code()
    persian = sender.last_code.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    assert verify(persian).status_code == 200


def test_verify_code_format_is_validated(sender):
    request_code()
    for bad in ("123", "abcdef", "1234567"):
        response = verify(bad)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_request_code_ip_rate_limit(sender):
    for i in range(10):
        assert request_code(f"0912123{i:04d}").status_code == 200
    limited = request_code("09125550000")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"


def test_sms_disabled_by_default(api_db, secret_key, monkeypatch):
    monkeypatch.setenv("PHONE_HASH_KEY", "k")
    monkeypatch.delenv("SMS_PROVIDER", raising=False)
    response = request_code()
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SMS_DISABLED"


def test_auth_disabled_without_phone_hash_key(sender, monkeypatch):
    monkeypatch.delenv("PHONE_HASH_KEY")
    response = request_code()
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_DISABLED"
    assert sender.sent == []


def test_me_requires_login(secret_key):
    assert client.get(f"{AUTH}/me").status_code == 401


def test_full_journey_login_then_review(sender):
    request_code()
    token = verify(sender.last_code).json()["accessToken"]
    response = client.post(
        "/api/v1/teachers/2/reviews",
        json={
            "reviewerLabel": "فارغ‌التحصیل",
            "stars": 4,
            "recommends": True,
            "body": "تجربه‌ی خوبی بود.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"