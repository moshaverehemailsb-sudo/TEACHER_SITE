from fastapi.testclient import TestClient

from app.deps import get_db
from app.main import app
from app.models import Review

client = TestClient(app)


def test_reviews_of_teacher_with_reviews():
    data = client.get("/api/v1/teachers/1/reviews").json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["pageSize"] == 10
    assert sorted(item["stars"] for item in data["items"]) == [4, 5, 5]
    assert all(item["recommends"] is True for item in data["items"])


def test_review_items_expose_only_public_fields():
    item = client.get("/api/v1/teachers/1/reviews").json()["items"][0]
    assert set(item) == {"id", "reviewerLabel", "stars", "recommends", "body", "createdAt"}
    labels = {
        i["reviewerLabel"]
        for i in client.get("/api/v1/teachers/1/reviews").json()["items"]
    }
    assert labels == {
        "دانش‌آموز پایه دوازدهم",
        "فارغ‌التحصیل",
        "دانش‌آموز پایه یازدهم",
    }


def test_teacher_without_reviews_returns_empty_list():
    data = client.get("/api/v1/teachers/2/reviews").json()
    assert data["total"] == 0
    assert data["items"] == []


def test_reviews_pagination():
    data = client.get("/api/v1/teachers/1/reviews", params={"page": 2, "pageSize": 2}).json()
    assert data["total"] == 3
    assert len(data["items"]) == 1


def test_reviews_of_missing_teacher_is_404():
    response = client.get("/api/v1/teachers/9999/reviews")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TEACHER_NOT_FOUND"


def test_non_approved_reviews_are_hidden_and_not_counted(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        for status in ("pending", "rejected", "hidden"):
            db.add(
                Review(
                    teacher_id=2,
                    user_id=None,
                    is_imported=True,
                    overall_rating=1,
                    body=f"{status} review",
                    status=status,
                )
            )
        db.flush()

        reviews = client.get("/api/v1/teachers/2/reviews").json()
        assert reviews["total"] == 0
        assert reviews["items"] == []

        profile = client.get("/api/v1/teachers/2").json()
        assert profile["rating"] is None
        assert profile["reviewCount"] == 0
    finally:
        app.dependency_overrides.clear()
        