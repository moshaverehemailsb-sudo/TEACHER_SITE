from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unknown_path_uses_error_format():
    response = client.get("/api/v1/nothing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_uses_error_format():
    response = client.get("/api/v1/teachers", params={"pageSize": 500})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["field"] == "query.pageSize"


def test_wrong_method_uses_error_format():
    response = client.post("/api/v1/subjects")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_security_headers_are_set():
    response = client.get("/api/v1/subjects")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"