from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_subjects_endpoint():
    response = client.get("/api/v1/subjects")
    data = response.json()
    assert response.status_code == 200
    assert data["top"] == ["ریاضی", "زیست", "شیمی"]
    assert len(data["subjects"]) == 16
    assert [len(g["options"]) for g in data["groups"]] == [7, 5, 8, 6]
    