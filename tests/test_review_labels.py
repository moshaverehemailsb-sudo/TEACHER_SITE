from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def post(headers, label):
    return client.post(
        "/api/v1/teachers/2/reviews",
        json={
            "reviewerLabel": label,
            "stars": 5,
            "recommends": True,
            "body": "نظر آزمایشی",
        },
        headers=headers,
    )


def test_label_is_accepted_with_or_without_zwnj(make_user):
    _, first = make_user(subject="label-1")
    _, second = make_user(subject="label-2")
    assert post(first, "دانش\u200cآموز پایه دهم").status_code == 201
    assert post(second, "دانشآموز پایه دهم").status_code == 201


def test_unknown_label_is_rejected(make_user):
    _, headers = make_user()
    response = post(headers, "هر چیز دیگری")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"