from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
URL = "/api/v1/teachers"


def test_list_default_first_page():
    data = client.get(URL).json()
    assert data["total"] == 39
    assert data["page"] == 1
    assert data["pageSize"] == 12
    assert len(data["items"]) == 12
    assert data["items"][0]["id"] == 1


def test_last_page_has_remaining_items():
    data = client.get(URL, params={"page": 4}).json()
    assert len(data["items"]) == 3


def test_filter_by_subject():
    data = client.get(URL, params={"subject": "فیزیک"}).json()
    assert data["total"] == 19
    assert all(item["subject"] == "فیزیک" for item in data["items"])


def test_search_normalizes_text():
    assert client.get(URL, params={"q": "مومن زاده"}).json()["total"] == 1
    assert client.get(URL, params={"q": "مومنزاده"}).json()["total"] == 1


def test_popular_sort_puts_reviewed_teachers_first():
    items = client.get(URL, params={"sort": "popular"}).json()["items"]
    assert [i["id"] for i in items[:2]] == [1, 3]
    assert items[0]["reviewCount"] == 3
    assert items[0]["rating"] == 4.7
    assert items[0]["recommendPercent"] == 100
    assert items[2]["rating"] is None
    assert items[2]["reviewCount"] == 0


def test_card_has_tags_photo_and_style():
    first = client.get(URL, params={"sort": "popular"}).json()["items"][0]
    assert first["photoUrl"] == "assets/teachers/1.jpg"
    assert first["tags"] == ["رسمی", "تست زیاد"]
    assert first["style"] == "کامل و تکنیکی"
    assert first["level"]


def test_scratch_filter_matches_style_exactly():
    assert client.get(URL, params={"scratch": 1}).json()["total"] == 0


def test_page_size_limit():
    assert client.get(URL, params={"pageSize": 500}).status_code == 422