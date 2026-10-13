from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Review, ReviewAnswer, ReviewQuestion
from app.schemas.reviews import ReviewListOut, ReviewOut
from app.services.lookup import get_active_teacher

router = APIRouter(tags=["reviews"])


@router.get("/teachers/{teacher_id}/reviews", response_model=ReviewListOut)
def list_reviews(
    teacher_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50, alias="pageSize"),
    db: Session = Depends(get_db),
):
    get_active_teacher(db, teacher_id)

    approved = [Review.teacher_id == teacher_id, Review.status == "approved"]
    total = db.scalar(select(func.count()).select_from(Review).where(*approved))

    recommend = (
        select(
            ReviewAnswer.review_id.label("review_id"),
            ReviewAnswer.value.label("value"),
        )
        .join(ReviewQuestion, ReviewQuestion.id == ReviewAnswer.question_id)
        .where(ReviewQuestion.key == "would_recommend")
        .subquery()
    )
    rows = db.execute(
        select(Review, recommend.c.value)
        .outerjoin(recommend, recommend.c.review_id == Review.id)
        .where(*approved)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        ReviewOut(
            id=review.id,
            reviewer_label=review.educational_stage,
            stars=review.overall_rating,
            recommends=None if value is None else bool(value),
            body=review.body,
            created_at=review.created_at,
        )
        for review, value in rows
    ]
    return ReviewListOut(items=items, total=total, page=page, page_size=page_size)