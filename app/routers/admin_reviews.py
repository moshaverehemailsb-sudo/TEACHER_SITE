from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.errors import ApiError
from app.models import Review, ReviewAnswer
from app.schemas.admin import AdminReviewListOut, AdminReviewOut, ModerationIn
from app.security import require_admin

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def to_admin_out(review: Review) -> AdminReviewOut:
    value = next(
        (a.value for a in review.answers if a.question.key == "would_recommend"),
        None,
    )
    return AdminReviewOut(
        id=review.id,
        teacher_id=review.teacher_id,
        teacher_name=review.teacher.full_name,
        reviewer_label=review.educational_stage,
        stars=review.overall_rating,
        recommends=None if value is None else bool(value),
        body=review.body,
        status=review.status,
        is_imported=review.is_imported,
        moderation_note=review.moderation_note,
        moderated_at=review.moderated_at,
        created_at=review.created_at,
    )


@router.get("/reviews", response_model=AdminReviewListOut)
def list_reviews(
    status: Literal["pending", "approved", "rejected", "hidden", "all"] = "pending",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
):
    filters = [] if status == "all" else [Review.status == status]
    total = db.scalar(select(func.count()).select_from(Review).where(*filters))

    # صف بررسی: قدیمی‌ترین اول؛ بقیه: تازه‌ترین اول
    if status == "pending":
        order = [Review.created_at, Review.id]
    else:
        order = [Review.created_at.desc(), Review.id.desc()]

    reviews = db.scalars(
        select(Review)
        .where(*filters)
        .options(
            selectinload(Review.teacher),
            selectinload(Review.answers).selectinload(ReviewAnswer.question),
        )
        .order_by(*order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return AdminReviewListOut(
        items=[to_admin_out(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/reviews/{review_id}", response_model=AdminReviewOut)
def moderate_review(
    review_id: int, body: ModerationIn, db: Session = Depends(get_db)
):
    review = db.get(Review, review_id)
    if review is None:
        raise ApiError(404, "REVIEW_NOT_FOUND", "نظر پیدا نشد.")

    review.status = body.status
    review.moderation_note = body.note
    review.moderated_at = (
        None if body.status == "pending" else datetime.now(timezone.utc)
    )
    db.commit()
    return to_admin_out(review)