from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Teacher
from app.schemas.teachers import TeacherCardOut
from app.services.teacher_cards import build_stats, load_tags, to_card


def load_cards(db: Session, teachers: list[Teacher]) -> dict[int, TeacherCardOut]:
    ids = [t.id for t in teachers]
    if not ids:
        return {}

    stats, recommend = build_stats(ids)
    rows = db.execute(
        select(Teacher.id, stats.c.review_count, stats.c.rating, recommend.c.recommend)
        .outerjoin(stats, stats.c.teacher_id == Teacher.id)
        .outerjoin(recommend, recommend.c.teacher_id == Teacher.id)
        .where(Teacher.id.in_(ids))
    ).all()
    numbers = {tid: (count, rating, rec) for tid, count, rating, rec in rows}
    tags = load_tags(db, ids)
    return {t.id: to_card(t, *numbers[t.id], tags.get(t.id, [])) for t in teachers}