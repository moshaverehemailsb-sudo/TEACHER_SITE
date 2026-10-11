from sqlalchemy import func, select

from app.models import Subject


def test_insert_inside_transaction(db):
    db.add(Subject(name="Test", slug="test"))
    db.flush()
    count = db.scalar(select(func.count()).select_from(Subject).where(Subject.slug == "test"))
    assert count == 1


def test_previous_test_left_no_data(db):
    count = db.scalar(select(func.count()).select_from(Subject).where(Subject.slug == "test"))
    assert count == 0
    