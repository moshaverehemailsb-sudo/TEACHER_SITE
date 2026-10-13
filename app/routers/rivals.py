from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.models import Subject, Teacher
from app.schemas.rivals import RivalListOut
from app.services.lookup import get_active_teacher
from app.services.teacher_cards import build_stats, load_tags, to_card

router = APIRouter(tags=["teachers"])


@router.get("/teachers/{teacher_id}/rivals", response_model=RivalListOut)
def list_rivals(
    teacher_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    teacher = get_active_teacher(db, teacher_id, selectinload(Teacher.subjects))
    subject_ids = [s.id for s in teacher.subjects]
    if not subject_ids:
        return RivalListOut(items=[])

    stats, recommend = build_stats()
    rows = db.execute(
        select(Teacher, stats.c.review_count, stats.c.rating, recommend.c.recommend)
        .outerjoin(stats, stats.c.teacher_id == Teacher.id)
        .outerjoin(recommend, recommend.c.teacher_id == Teacher.id)
        .where(
            Teacher.is_active.is_(True),
            Teacher.id != teacher.id,
            Teacher.subjects.any(Subject.id.in_(subject_ids)),
        )
        .options(selectinload(Teacher.subjects))
        .order_by(
            stats.c.rating.desc().nulls_last(),
            stats.c.review_count.desc().nulls_last(),
            Teacher.id,
        )
        .limit(limit)
    ).all()

    tags = load_tags(db, [row[0].id for row in rows])
    items = [
        to_card(t, count, rating, rec, tags.get(t.id, []))
        for t, count, rating, rec in rows
    ]
    return RivalListOut(items=items)