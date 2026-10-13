from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.errors import ApiError
from app.models import Subject, Teacher, teacher_subjects
from app.schemas.teachers import (
    BioOut,
    CourseOut,
    TeacherListOut,
    TeacherProfileOut,
)
from app.services.teacher_cards import build_stats, load_card, load_tags, to_card
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


@router.get("/teachers/{teacher_id}", response_model=TeacherProfileOut)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.scalar(
        select(Teacher)
        .where(Teacher.id == teacher_id, Teacher.is_active.is_(True))
        .options(
            selectinload(Teacher.subjects),
            selectinload(Teacher.detail),
            selectinload(Teacher.courses),
        )
    )
    if teacher is None:
        raise ApiError(404, "TEACHER_NOT_FOUND", "استاد پیدا نشد.")

    card = load_card(db, teacher)
    bio = teacher.detail
    courses = sorted(
        (c for c in teacher.courses if c.status == "published"),
        key=lambda c: (c.sort_order, c.id),
    )
    return TeacherProfileOut(
        **card.model_dump(),
        bio=(
            BioOut(
                class_style=bio.class_style,
                method=bio.method,
                level_text=bio.level_text,
                problem_solving=bio.problem_solving,
                education=bio.education,
                experience=bio.experience,
                note=bio.note,
            )
            if bio
            else None
        ),
        courses=[
            CourseOut(id=c.id, title=c.title, description=c.description)
            for c in courses
        ],
    )