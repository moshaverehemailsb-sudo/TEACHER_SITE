from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_profile_with_reviews_bio_and_courses():
    data = client.get("/api/v1/teachers/1").json()
    assert data["name"] == "امید مصلایی"
    assert data["subject"] == "شیمی"
    assert data["rating"] == 4.7
    assert data["reviewCount"] == 3
    assert data["recommendPercent"] == 100
    assert data["tags"] == ["رسمی", "تست زیاد"]
    assert data["bio"]["experience"] == "۱۲ سال سابقه تدریس شیمی کنکور"
    assert data["bio"]["note"] is None
    assert [c["title"] for c in data["courses"]] == [
        "دوره سالیانه",
        "دوره مینی سالیانه",
        "دوره نکته و تست",
    ]


def test_profile_with_four_courses_in_order():
    data = client.get("/api/v1/teachers/3").json()
    assert len(data["courses"]) == 4
    assert data["courses"][-1]["title"] == "کمربند مشکی"


def test_profile_without_bio_courses_or_reviews():
    data = client.get("/api/v1/teachers/2").json()
    assert data["bio"] is None
    assert data["courses"] == []
    assert data["rating"] is None
    assert data["reviewCount"] == 0
    assert data["recommendPercent"] is None


def test_education_keeps_multiple_lines():
    data = client.get("/api/v1/teachers/36").json()
    assert data["bio"]["education"].count("\n") == 1
    assert data["bio"]["classStyle"]


def test_missing_teacher_returns_error_format():
    response = client.get("/api/v1/teachers/9999")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "TEACHER_NOT_FOUND", "message": "استاد پیدا نشد."}
    }
    