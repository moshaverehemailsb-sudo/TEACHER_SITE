from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.errors import ApiError
from app.models import PopularComparison, Teacher
from app.schemas.compare import (
    CompareOut,
    CompareTeacherOut,
    PopularComparisonListOut,
    PopularComparisonOut,
)
from app.services.card_batch import load_cards
from app.services.lookup import get_active_teacher
from app.services.teacher_cards import load_card

router = APIRouter(tags=["compare"])


def compare_item(db: Session, teacher: Teacher) -> CompareTeacherOut:
    card = load_card(db, teacher)
    bio = teacher.detail
    return CompareTeacherOut(
        **card.model_dump(),
        education=bio.education if bio else None,
        experience=bio.experience if bio else None,
    )


@router.get("/compare", response_model=CompareOut)
def compare(a: int | None = None, b: int | None = None, db: Session = Depends(get_db)):
    if a is None or b is None:
        raise ApiError(400, "COMPARE_MISSING_IDS", "هر دو استاد را انتخاب کن.")
    if a == b:
        raise ApiError(400, "COMPARE_SAME_TEACHER", "دو استاد باید متفاوت باشند.")

    options = (selectinload(Teacher.subjects), selectinload(Teacher.detail))
    teacher_a = get_active_teacher(db, a, *options)
    teacher_b = get_active_teacher(db, b, *options)

    subjects_b = {s.id for s in teacher_b.subjects}
    shared = [s for s in teacher_a.subjects if s.id in subjects_b]
    if not shared:
        raise ApiError(
            400,
            "COMPARE_DIFFERENT_SUBJECT",
            "فقط استادهای هم‌درس را می‌توان مقایسه کرد.",
        )
    subject = min(shared, key=lambda s: s.sort_order)

    return CompareOut(
        subject=subject.name,
        a=compare_item(db, teacher_a),
        b=compare_item(db, teacher_b),
    )


@router.get("/popular-comparisons", response_model=PopularComparisonListOut)
def list_popular_comparisons(db: Session = Depends(get_db)):
    pairs = db.scalars(
        select(PopularComparison)
        .options(
            selectinload(PopularComparison.teacher_a).selectinload(Teacher.subjects),
            selectinload(PopularComparison.teacher_b).selectinload(Teacher.subjects),
        )
        .order_by(PopularComparison.sort_order, PopularComparison.id)
    ).all()
    pairs = [p for p in pairs if p.teacher_a.is_active and p.teacher_b.is_active]

    teachers: dict[int, Teacher] = {}
    for pair in pairs:
        teachers[pair.teacher_a.id] = pair.teacher_a
        teachers[pair.teacher_b.id] = pair.teacher_b
    cards = load_cards(db, list(teachers.values()))

    return PopularComparisonListOut(
        items=[
            PopularComparisonOut(
                id=p.id,
                label=p.label,
                a=cards[p.teacher_a_id],
                b=cards[p.teacher_b_id],
            )
            for p in pairs
        ]
    )