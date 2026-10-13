from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Review, ReviewAnswer, ReviewQuestion, Tag, Teacher, TeacherTag
from app.schemas.teachers import TeacherCardOut

# فقط این منبع‌ها عمومی نمایش داده می‌شوند؛ ai_inferred تأییدشده حساب نمی‌شود
PUBLIC_TAG_SOURCES = ("verified", "student_reported")


def build_stats(teacher_ids: list[int] | None = None):
    """میانگین نمره و تعداد نظر و درصد توصیه، فقط از نظرهای تأییدشده."""
    review_filters = [Review.status == "approved"]
    if teacher_ids is not None:
        review_filters.append(Review.teacher_id.in_(teacher_ids))

    stats = (
        select(
            Review.teacher_id.label("teacher_id"),
            func.count(Review.id).label("review_count"),
            func.avg(Review.overall_rating).label("rating"),
        )
        .where(*review_filters)
        .group_by(Review.teacher_id)
        .subquery()
    )
    recommend = (
        select(
            Review.teacher_id.label("teacher_id"),
            (func.avg(ReviewAnswer.value) * 100).label("recommend"),
        )
        .join(ReviewAnswer, ReviewAnswer.review_id == Review.id)
        .join(ReviewQuestion, ReviewQuestion.id == ReviewAnswer.question_id)
        .where(*review_filters, ReviewQuestion.key == "would_recommend")
        .group_by(Review.teacher_id)
        .subquery()
    )
    return stats, recommend


def load_tags(db: Session, teacher_ids: list[int]) -> dict[int, list[str]]:
    rows = db.execute(
        select(TeacherTag.teacher_id, Tag.name)
        .join(Tag, Tag.id == TeacherTag.tag_id)
        .where(
            TeacherTag.teacher_id.in_(teacher_ids),
            TeacherTag.source.in_(PUBLIC_TAG_SOURCES),
        )
        .order_by(Tag.id)
    ).all()
    tags: dict[int, list[str]] = {}
    for teacher_id, name in rows:
        names = tags.setdefault(teacher_id, [])
        if name not in names:
            names.append(name)
    return tags


def to_card(teacher: Teacher, review_count, rating, recommend, tags: list[str]) -> TeacherCardOut:
    subject = (
        min(teacher.subjects, key=lambda s: s.sort_order).name
        if teacher.subjects
        else None
    )
    return TeacherCardOut(
        id=teacher.id,
        name=teacher.full_name,
        subject=subject,
        style=teacher.teaching_style,
        level=teacher.suitable_level,
        tags=tags,
        photo_url=teacher.profile_image_url,
        rating=round(float(rating), 1) if rating is not None else None,
        review_count=review_count or 0,
        recommend_percent=round(float(recommend)) if recommend is not None else None,
    )


def load_card(db: Session, teacher: Teacher) -> TeacherCardOut:
    stats, recommend = build_stats([teacher.id])
    review_count, rating, rec = db.execute(
        select(stats.c.review_count, stats.c.rating, recommend.c.recommend)
        .select_from(Teacher)
        .outerjoin(stats, stats.c.teacher_id == Teacher.id)
        .outerjoin(recommend, recommend.c.teacher_id == Teacher.id)
        .where(Teacher.id == teacher.id)
    ).one()
    tags = load_tags(db, [teacher.id]).get(teacher.id, [])
    return to_card(teacher, review_count, rating, rec, tags)