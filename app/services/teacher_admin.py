from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Subject, Tag, Teacher, TeacherTag
from app.schemas.admin import AdminTeacherOut
from app.text import normalize_search, slugify_tag


def clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def find_subjects(db: Session, names: list[str]) -> list[Subject]:
    names = list(dict.fromkeys(names))
    by_name = {
        s.name: s for s in db.scalars(select(Subject).where(Subject.name.in_(names)))
    }
    missing = [name for name in names if name not in by_name]
    if missing:
        raise ApiError(
            400, "SUBJECT_NOT_FOUND", "درس نامعتبر است: " + "، ".join(missing)
        )
    return [by_name[name] for name in names]


def verified_tag_names(db: Session, teacher_id: int) -> list[str]:
    return list(
        db.scalars(
            select(Tag.name)
            .join(TeacherTag, TeacherTag.tag_id == Tag.id)
            .where(
                TeacherTag.teacher_id == teacher_id,
                TeacherTag.source == "verified",
            )
            .order_by(Tag.id)
        )
    )


def set_verified_tags(db: Session, teacher: Teacher, names: list[str]) -> None:
    """فقط تگ‌های verified را عوض می‌کند؛ تگ‌های student_reported و ai_inferred دست‌نخورده می‌مانند."""
    names = list(dict.fromkeys(names))
    tags_by_name = (
        {t.name: t for t in db.scalars(select(Tag).where(Tag.name.in_(names)))}
        if names
        else {}
    )
    wanted_ids: set[int] = set()
    for name in names:
        tag = tags_by_name.get(name)
        if tag is None:
            tag = Tag(name=name, slug=slugify_tag(name))
            db.add(tag)
            db.flush()
        wanted_ids.add(tag.id)

    links = db.scalars(
        select(TeacherTag).where(
            TeacherTag.teacher_id == teacher.id, TeacherTag.source == "verified"
        )
    ).all()
    have = {link.tag_id for link in links}
    for link in links:
        if link.tag_id not in wanted_ids:
            db.delete(link)
    for tag_id in wanted_ids - have:
        db.add(TeacherTag(teacher_id=teacher.id, tag_id=tag_id, source="verified"))
    db.flush()


def refresh_search(db: Session, teacher: Teacher) -> None:
    parts = [
        teacher.full_name,
        *[s.name for s in teacher.subjects],
        teacher.teaching_style or "",
        *verified_tag_names(db, teacher.id),
    ]
    teacher.normalized_search = normalize_search(" ".join(parts))


def to_admin_out(db: Session, teacher: Teacher) -> AdminTeacherOut:
    return AdminTeacherOut(
        id=teacher.id,
        slug=teacher.slug,
        name=teacher.full_name,
        subjects=[s.name for s in sorted(teacher.subjects, key=lambda s: s.sort_order)],
        style=teacher.teaching_style,
        level=teacher.suitable_level,
        tags=verified_tag_names(db, teacher.id),
        photo_url=teacher.profile_image_url,
        is_active=teacher.is_active,
    )