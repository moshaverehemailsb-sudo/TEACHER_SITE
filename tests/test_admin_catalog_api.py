from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ADMIN = "/api/v1/admin"
PUBLIC = "/api/v1"


def create_teacher(headers, **overrides):
    body = {
        "name": "استاد آزمایشی",
        "subjects": ["شیمی"],
        "style": "مفهومی",
        "tags": ["تگ جدید"],
    }
    body.update(overrides)
    return client.post(f"{ADMIN}/teachers", json=body, headers=headers)


def test_catalog_admin_requires_token(admin_headers):
    response = client.post(
        f"{ADMIN}/teachers", json={"name": "x", "subjects": ["شیمی"]}
    )
    assert response.status_code == 401


def test_admin_can_create_teacher(api_db, admin_headers):
    response = create_teacher(admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "استاد آزمایشی"
    assert data["subjects"] == ["شیمی"]
    assert data["tags"] == ["تگ جدید"]
    assert data["isActive"] is True
    assert data["slug"] == f"t-{data['id']}"

    found = client.get(f"{PUBLIC}/teachers", params={"q": "آزمایشی"}).json()
    assert found["total"] == 1
    assert found["items"][0]["id"] == data["id"]
    assert found["items"][0]["subject"] == "شیمی"
    assert found["items"][0]["tags"] == ["تگ جدید"]


def test_create_teacher_with_unknown_subject_is_rejected(api_db, admin_headers):
    response = create_teacher(admin_headers, subjects=["نامعتبر"])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SUBJECT_NOT_FOUND"


def test_create_teacher_requires_name(api_db, admin_headers):
    response = create_teacher(admin_headers, name="   ")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_teacher_style_and_tags(api_db, admin_headers):
    response = client.patch(
        f"{ADMIN}/teachers/2",
        json={"style": "آموزش از پایه", "tags": ["مفهومی"]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["style"] == "آموزش از پایه"
    assert response.json()["tags"] == ["مفهومی"]

    profile = client.get(f"{PUBLIC}/teachers/2").json()
    assert profile["tags"] == ["مفهومی"]
    assert client.get(f"{PUBLIC}/teachers", params={"scratch": 1}).json()["total"] == 1


def test_deactivated_teacher_disappears_from_public_api(api_db, admin_headers):
    response = client.patch(
        f"{ADMIN}/teachers/2", json={"isActive": False}, headers=admin_headers
    )
    assert response.json()["isActive"] is False
    assert client.get(f"{PUBLIC}/teachers/2").status_code == 404
    assert client.get(f"{PUBLIC}/teachers").json()["total"] == 38


def test_photo_url_must_be_safe(api_db, admin_headers):
    bad = client.patch(
        f"{ADMIN}/teachers/2",
        json={"photoUrl": "javascript:alert(1)"},
        headers=admin_headers,
    )
    assert bad.status_code == 422

    good = client.patch(
        f"{ADMIN}/teachers/2",
        json={"photoUrl": "assets/teachers/2.jpg"},
        headers=admin_headers,
    )
    assert good.status_code == 200
    assert client.get(f"{PUBLIC}/teachers/2").json()["photoUrl"] == "assets/teachers/2.jpg"


def test_update_missing_teacher_is_404(api_db, admin_headers):
    response = client.patch(
        f"{ADMIN}/teachers/9999", json={"style": "x"}, headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TEACHER_NOT_FOUND"


def test_bio_upsert_replaces_all_fields(api_db, admin_headers):
    response = client.put(
        f"{ADMIN}/teachers/2/bio",
        json={"experience": "۵ سال سابقه", "education": "کارشناسی"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["experience"] == "۵ سال سابقه"
    assert response.json()["classStyle"] is None
    assert client.get(f"{PUBLIC}/teachers/2").json()["bio"]["education"] == "کارشناسی"

    response = client.put(
        f"{ADMIN}/teachers/2/bio",
        json={"experience": "۶ سال سابقه"},
        headers=admin_headers,
    )
    assert response.json()["education"] is None
    assert response.json()["experience"] == "۶ سال سابقه"


def test_course_create_and_archive(api_db, admin_headers):
    response = client.post(
        f"{ADMIN}/teachers/1/courses",
        json={"title": "دوره جدید", "description": "توضیح"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    course = response.json()
    assert course["sortOrder"] == 4
    assert course["status"] == "published"
    assert course["teacherIds"] == [1]

    titles = [c["title"] for c in client.get(f"{PUBLIC}/teachers/1").json()["courses"]]
    assert len(titles) == 4
    assert titles[-1] == "دوره جدید"

    response = client.patch(
        f"{ADMIN}/courses/{course['id']}",
        json={"status": "archived"},
        headers=admin_headers,
    )
    assert response.json()["status"] == "archived"
    assert len(client.get(f"{PUBLIC}/teachers/1").json()["courses"]) == 3


def test_update_missing_course_is_404(api_db, admin_headers):
    response = client.patch(
        f"{ADMIN}/courses/999999", json={"status": "archived"}, headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COURSE_NOT_FOUND"


def test_popular_comparison_lifecycle(api_db, admin_headers):
    response = client.post(
        f"{ADMIN}/popular-comparisons",
        json={"teacherAId": 7, "teacherBId": 8, "label": "مقایسه‌ی شیمی"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    pair = response.json()
    assert pair["sortOrder"] == 7

    items = client.get(f"{PUBLIC}/popular-comparisons").json()["items"]
    assert len(items) == 7
    assert (items[-1]["a"]["id"], items[-1]["b"]["id"]) == (7, 8)

    duplicate = client.post(
        f"{ADMIN}/popular-comparisons",
        json={"teacherAId": 8, "teacherBId": 7, "label": "x"},
        headers=admin_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PAIR_EXISTS"

    deleted = client.delete(
        f"{ADMIN}/popular-comparisons/{pair['id']}", headers=admin_headers
    )
    assert deleted.status_code == 204
    assert len(client.get(f"{PUBLIC}/popular-comparisons").json()["items"]) == 6


def test_popular_comparison_must_be_same_subject(api_db, admin_headers):
    response = client.post(
        f"{ADMIN}/popular-comparisons",
        json={"teacherAId": 1, "teacherBId": 20, "label": "x"},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "COMPARE_DIFFERENT_SUBJECT"


def test_popular_comparison_rejects_same_teacher(api_db, admin_headers):
    response = client.post(
        f"{ADMIN}/popular-comparisons",
        json={"teacherAId": 1, "teacherBId": 1, "label": "x"},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "COMPARE_SAME_TEACHER"


def test_delete_missing_pair_is_404(api_db, admin_headers):
    response = client.delete(
        f"{ADMIN}/popular-comparisons/999999", headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAIR_NOT_FOUND"