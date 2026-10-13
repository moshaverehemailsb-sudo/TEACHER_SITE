from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.models import Subject, Teacher, teacher_subjects
from app.schemas.teachers import TeacherListOut
from app.services.teacher_cards import build_stats, load_tags, to_card
from app.text import normalize_search

router = APIRouter(tags=["teachers"])

SCRATCH_STYLE = "آموزش از پایه"


@router.get("/teachers", response_model=TeacherListOut)
def list_teachers(
    subject: str | None = None,
    q: str | None = None,
    sort: Literal["popular", "reviews", "default"] = "default",
    scratch: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50, alias="pageSize"),
    db: Session = Depends(get_db),
):
    filters = [Teacher.is_active.is_(True)]
    if subject:
        filters.append(Teacher.subjects.any(Subject.name == subject))
    normalized_q = normalize_search(q) if q else ""
    if normalized_q:
        filters.append(
            Teacher.normalized_search.contains(normalized_q, autoescape=True)
        )
    if scratch:
        filters.append(Teacher.teaching_style == SCRATCH_STYLE)

    total = db.scalar(select(func.count()).select_from(Teacher).where(*filters))

    stats, recommend = build_stats()
    subject_order = (
        select(func.min(Subject.sort_order))
        .join(teacher_subjects, teacher_subjects.c.subject_id == Subject.id)
        .where(teacher_subjects.c.teacher_id == Teacher.id)
        .scalar_subquery()
    )

    if sort == "popular":
        order = [
            recommend.c.recommend.desc().nulls_last(),
            stats.c.rating.desc().nulls_last(),
            Teacher.id,
        ]
    elif sort == "reviews":
        order = [stats.c.review_count.desc().nulls_last(), Teacher.id]
    else:
        order = [subject_order, Teacher.id]

    rows = db.execute(
        select(Teacher, stats.c.review_count, stats.c.rating, recommend.c.recommend)
        .outerjoin(stats, stats.c.teacher_id == Teacher.id)
        .outerjoin(recommend, recommend.c.teacher_id == Teacher.id)
        .where(*filters)
        .options(selectinload(Teacher.subjects))
        .order_by(*order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    tags = load_tags(db, [row[0].id for row in rows])
    items = [
        to_card(teacher, count, rating, rec, tags.get(teacher.id, []))
        for teacher, count, rating, rec in rows
    ]
    return TeacherListOut(items=items, total=total, page=page, page_size=page_size)