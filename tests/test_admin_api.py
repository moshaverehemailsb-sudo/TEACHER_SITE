from fastapi.testclient import TestClient

from app.main import app
from app.models import Review

client = TestClient(app)
URL = "/api/v1/admin/reviews"


def add_review(db, teacher_id=2, stars=4, status="pending", body="test review"):
    review = Review(
        teacher_id=teacher_id,
        user_id=None,
        is_imported=True,
        overall_rating=stars,
        body=body,
        status=status,
    )
    db.add(review)
    db.flush()
    return review


def test_admin_requires_token(admin_headers):
    response = client.get(URL)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_rejects_wrong_token(admin_headers):
    response = client.get(URL, headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_admin_disabled_without_configured_token(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    response = client.get(URL, headers={"Authorization": "Bearer anything"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ADMIN_DISABLED"


def test_pending_queue_lists_new_reviews(api_db, admin_headers):
    review = add_review(api_db)
    data = client.get(URL, headers=admin_headers).json()
    assert review.id in [item["id"] for item in data["items"]]
    assert all(item["status"] == "pending" for item in data["items"])


def test_admin_review_exposes_internal_fields(api_db, admin_headers):
    review = add_review(api_db)
    items = client.get(URL, headers=admin_headers).json()["items"]
    item = next(i for i in items if i["id"] == review.id)
    assert item["teacherName"] == "محمد علی مومن زاده"
    assert item["isImported"] is True
    assert item["moderationNote"] is None
    assert item["status"] == "pending"


def test_moderation_changes_status_and_public_stats(api_db, admin_headers):
    review = add_review(api_db, teacher_id=2, stars=4)
    assert client.get("/api/v1/teachers/2").json()["reviewCount"] == 0

    response = client.patch(
        f"{URL}/{review.id}", json={"status": "approved"}, headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["moderatedAt"] is not None
    profile = client.get("/api/v1/teachers/2").json()
    assert profile["reviewCount"] == 1
    assert profile["rating"] == 4.0
    assert client.get("/api/v1/teachers/2/reviews").json()["total"] == 1

    response = client.patch(
        f"{URL}/{review.id}",
        json={"status": "hidden", "note": "spam"},
        headers=admin_headers,
    )
    assert response.json()["moderationNote"] == "spam"
    assert client.get("/api/v1/teachers/2").json()["reviewCount"] == 0


def test_moderation_rejects_invalid_status(api_db, admin_headers):
    review = add_review(api_db)
    response = client.patch(
        f"{URL}/{review.id}", json={"status": "published"}, headers=admin_headers
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_moderating_missing_review_is_404(api_db, admin_headers):
    response = client.patch(
        f"{URL}/999999999", json={"status": "approved"}, headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "REVIEW_NOT_FOUND"