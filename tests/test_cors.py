from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_allowed_origin_gets_cors_header():
    response = client.get(
        "/api/v1/subjects", headers={"Origin": "http://localhost:5500"}
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_unknown_origin_gets_no_cors_header():
    response = client.get(
        "/api/v1/subjects", headers={"Origin": "https://evil.example"}
    )
    assert "access-control-allow-origin" not in response.headers
    