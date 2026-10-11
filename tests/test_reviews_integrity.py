import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import Course, Review, Subject, Teacher, User


def make_base(db):
    subject = Subject(name="Physics", slug="physics")
    teacher = Teacher(slug="t-one", full_name="Teacher One")
    other_teacher = Teacher(slug="t-two", full_name="Teacher Two")
    user = User(display_name="Student", auth_provider="test", auth_subject="u1")
    db.add_all([subject, teacher, other_teacher, user])
    db.flush()

    course = Course(
        slug="c-one",
        title="Course One",
        subject_id=subject.id,
        course_type="recorded",
    )
    course.teachers.append(teacher)
    db.add(course)
    db.flush()
    return user, teacher, other_teacher, course


def make_review(user, teacher, course=None, **kwargs):
    data = dict(
        user_id=user.id,
        teacher_id=teacher.id,
        course_id=course.id if course else None,
        overall_rating=5,
        body="Good teacher",
    )
    data.update(kwargs)
    return Review(**data)


def test_new_review_defaults_to_pending(db):
    user, teacher, _, _ = make_base(db)
    review = make_review(user, teacher)
    db.add(review)
    db.flush()
    db.refresh(review)
    assert review.status == "pending"


def test_rating_out_of_range_is_rejected(db):
    user, teacher, _, _ = make_base(db)
    db.add(make_review(user, teacher, overall_rating=6))
    with pytest.raises(IntegrityError):
        db.flush()


def test_invalid_status_is_rejected(db):
    user, teacher, _, _ = make_base(db)
    db.add(make_review(user, teacher, status="published"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_course_review_requires_teacher_of_that_course(db):
    user, _, other_teacher, course = make_base(db)
    db.add(make_review(user, other_teacher, course))
    with pytest.raises(IntegrityError):
        db.flush()


def test_duplicate_review_without_course_is_rejected(db):
    user, teacher, _, _ = make_base(db)
    db.add(make_review(user, teacher))
    db.flush()
    db.add(make_review(user, teacher))
    with pytest.raises(IntegrityError):
        db.flush()


def test_teacher_review_and_course_review_can_coexist(db):
    user, teacher, _, course = make_base(db)
    db.add(make_review(user, teacher))
    db.add(make_review(user, teacher, course))
    db.flush()
    count = db.scalar(
        select(func.count()).select_from(Review).where(Review.user_id == user.id)
    )
    assert count == 2