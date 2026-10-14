from fastapi.testclient import TestClient

from app.main import app
from app.services.users import find_or_create_user

client = TestClient(app)
PUBLIC = "/api/v1"
ADMIN = "/api/v1/admin"


def valid_review(**overrides):
    payload = {
        "reviewerLabel": "دانش‌آموز پایه دوازدهم",
        "stars": 5,
        "recommends": True,
        "body": "کلاس خیلی خوب و مفهومی بود.",
    }
    payload.update(overrides)
    return payload


def post_review(headers, teacher_id=2, **overrides):
    return client.post(
        f"{PUBLIC}/teachers/{teacher_id}/reviews",
        json=valid_review(**overrides),
        headers=headers,
    )


def test_posting_review_requires_login(secret_key):
    response = client.post(f"{PUBLIC}/teachers/2/reviews", json=valid_review())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_invalid_token_is_rejected(secret_key):
    response = client.post(
        f"{PUBLIC}/teachers/2/reviews",
        json=valid_review(),
        headers={"Authorization": "Bearer garbage"},
    )
    assert response.status_code == 401


def test_login_is_disabled_without_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    response = client.post(
        f"{PUBLIC}/teachers/2/reviews",
        json=valid_review(),
        headers={"Authorization": "Bearer anything"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_DISABLED"


def test_token_of_inactive_user_is_rejected(make_user):
    _, headers = make_user(is_active=False)
    assert post_review(headers).status_code == 401


def test_review_flow_from_submission_to_public_stats(make_user, admin_headers):
    _, headers = make_user()
    response = post_review(headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["message"] == "نظر شما پس از بررسی نمایش داده می‌شود."

    assert client.get(f"{PUBLIC}/teachers/2/reviews").json()["total"] == 0
    assert client.get(f"{PUBLIC}/teachers/2").json()["reviewCount"] == 0

    queue = client.get(
        f"{ADMIN}/reviews", params={"pageSize": 100}, headers=admin_headers
    ).json()["items"]
    assert data["id"] in [item["id"] for item in queue]

    approved = client.patch(
        f"{ADMIN}/reviews/{data['id']}",
        json={"status": "approved"},
        headers=admin_headers,
    )
    assert approved.status_code == 200
    profile = client.get(f"{PUBLIC}/teachers/2").json()
    assert profile["reviewCount"] == 1
    assert profile["rating"] == 5.0
    assert profile["recommendPercent"] == 100
    item = client.get(f"{PUBLIC}/teachers/2/reviews").json()["items"][0]
    assert item["reviewerLabel"] == "دانش‌آموز پایه دوازدهم"
    assert item["recommends"] is True


def test_not_recommending_lowers_recommend_percent(make_user, admin_headers):
    _, headers = make_user()
    created = post_review(headers, stars=2, recommends=False).json()
    client.patch(
        f"{ADMIN}/reviews/{created['id']}",
        json={"status": "approved"},
        headers=admin_headers,
    )
    profile = client.get(f"{PUBLIC}/teachers/2").json()
    assert profile["rating"] == 2.0
    assert profile["recommendPercent"] == 0


def test_review_validation(make_user):
    _, headers = make_user()
    bad = [
        {"stars": 0},
        {"stars": 6},
        {"body": "   "},
        {"body": "x" * 1001},
        {"reviewerLabel": "معلم"},
    ]
    for overrides in bad:
        response = post_review(headers, **overrides)
        assert response.status_code == 422, overrides
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_html_is_stripped_from_review_text(make_user, admin_headers):
    _, headers = make_user()
    created = post_review(
        headers, body="<b>سلام</b><script>alert(1)</script> متن"
    ).json()
    queue = client.get(
        f"{ADMIN}/reviews", params={"pageSize": 100}, headers=admin_headers
    ).json()["items"]
    stored = next(i for i in queue if i["id"] == created["id"])["body"]
    assert "<" not in stored and ">" not in stored
    assert "سلام" in stored


def test_second_review_for_same_teacher_is_rejected(make_user):
    _, headers = make_user()
    assert post_review(headers).status_code == 201
    second = post_review(headers)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "REVIEW_EXISTS"


def test_review_for_missing_teacher_is_404(make_user):
    _, headers = make_user()
    response = post_review(headers, teacher_id=9999)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TEACHER_NOT_FOUND"


def test_review_rate_limit_per_user(make_user):
    _, headers = make_user()
    for teacher_id in range(2, 7):
        assert post_review(headers, teacher_id=teacher_id).status_code == 201
    limited = post_review(headers, teacher_id=7)
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"


def test_find_or_create_user_is_idempotent(db):
    first = find_or_create_user(db, "telegram", "123", "علی")
    again = find_or_create_user(db, "telegram", "123", "علی")
    other_provider = find_or_create_user(db, "phone", "123", "علی")
    assert first.id == again.id
    assert other_provider.id != first.id


def test_oversized_request_is_rejected():
    response = client.post(
        f"{PUBLIC}/teachers/2/reviews", json=valid_review(body="x" * 70000)
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_cors_preflight_allows_post_with_authorization():
    response = client.options(
        f"{PUBLIC}/teachers/2/reviews",
        headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"
    assert "POST" in response.headers["access-control-allow-methods"]