from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rivals_are_same_subject_sorted_by_rating():
    items = client.get("/api/v1/teachers/1/rivals").json()["items"]
    assert len(items) == 10
    assert items[0]["id"] == 3
    assert 1 not in [i["id"] for i in items]
    assert all(i["subject"] == "شیمی" for i in items)


def test_rivals_for_physics_teacher_are_physics():
    items = client.get("/api/v1/teachers/20/rivals").json()["items"]
    assert len(items) == 10
    assert all(i["subject"] == "فیزیک" for i in items)


def test_rivals_limit_is_validated():
    assert client.get("/api/v1/teachers/1/rivals", params={"limit": 100}).status_code == 422


def test_rivals_of_missing_teacher_is_404():
    response = client.get("/api/v1/teachers/9999/rivals")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TEACHER_NOT_FOUND"