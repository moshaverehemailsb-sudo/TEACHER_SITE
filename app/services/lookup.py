from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Teacher


def get_active_teacher(db: Session, teacher_id: int, *options) -> Teacher:
    teacher = db.scalar(
        select(Teacher)
        .where(Teacher.id == teacher_id, Teacher.is_active.is_(True))
        .options(*options)
    )
    if teacher is None:
        raise ApiError(404, "TEACHER_NOT_FOUND", "استاد پیدا نشد.")
    return teacher