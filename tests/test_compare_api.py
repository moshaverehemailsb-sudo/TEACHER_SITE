from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_compare_two_chemistry_teachers():
    data = client.get("/api/v1/compare", params={"a": 1, "b": 3}).json()
    assert data["subject"] == "شیمی"
    assert data["a"]["id"] == 1
    assert data["b"]["id"] == 3
    assert data["a"]["reviewCount"] == 3
    assert data["a"]["recommendPercent"] == 100
    assert data["a"]["education"] == "کارشناسی شیمی محض"
    assert data["b"]["education"] == "پزشکی از دانشگاه شیراز"
    assert data["b"]["experience"] == "سابقه تدریس شیمی کنکور"


def test_compare_teachers_without_bio_or_reviews():
    data = client.get("/api/v1/compare", params={"a": 2, "b": 4}).json()
    assert data["a"]["education"] is None
    assert data["a"]["experience"] is None
    assert data["a"]["rating"] is None
    assert data["b"]["reviewCount"] == 0


def test_compare_different_subjects_is_rejected():
    response = client.get("/api/v1/compare", params={"a": 1, "b": 20})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "COMPARE_DIFFERENT_SUBJECT"


def test_compare_same_teacher_is_rejected():
    response = client.get("/api/v1/compare", params={"a": 1, "b": 1})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "COMPARE_SAME_TEACHER"


def test_compare_missing_ids_is_rejected():
    for params in ({}, {"a": 1}, {"b": 3}):
        response = client.get("/api/v1/compare", params=params)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "COMPARE_MISSING_IDS"


def test_compare_missing_teacher_is_404():
    response = client.get("/api/v1/compare", params={"a": 1, "b": 9999})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TEACHER_NOT_FOUND"


def test_popular_comparisons_list():
    items = client.get("/api/v1/popular-comparisons").json()["items"]
    assert len(items) == 6
    assert items[0]["label"] == "مقایسه‌ی شیمی"
    assert (items[0]["a"]["id"], items[0]["b"]["id"]) == (1, 3)
    assert items[0]["a"]["reviewCount"] == 3
    assert (items[-1]["a"]["id"], items[-1]["b"]["id"]) == (24, 25)


def test_popular_comparisons_are_same_subject():
    items = client.get("/api/v1/popular-comparisons").json()["items"]
    assert all(i["a"]["subject"] == i["b"]["subject"] for i in items)