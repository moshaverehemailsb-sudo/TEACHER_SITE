from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.deps import get_db
from app.errors import ApiError
from app.models import Review, ReviewAnswer, ReviewQuestion, User
from app.ratelimit import review_limiter
from app.schemas.reviews import ReviewCreatedOut, ReviewIn, ReviewListOut, ReviewOut
from app.services.lookup import get_active_teacher
from app.text import clean_user_text

router = APIRouter(tags=["reviews"])

REVIEW_EXISTS_MESSAGE = "قبلاً برای این استاد نظر ثبت کرده‌ای."


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


@router.post(
    "/teachers/{teacher_id}/reviews",
    response_model=ReviewCreatedOut,
    status_code=201,
)
def create_review(
    teacher_id: int,
    body: ReviewIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_active_teacher(db, teacher_id)
    review_limiter.check(f"user:{user.id}")

    text = clean_user_text(body.body)
    if not text:
        raise ApiError(422, "VALIDATION_ERROR", "متن نظر نمی‌تواند خالی باشد.")

    question = db.scalar(
        select(ReviewQuestion).where(ReviewQuestion.key == "would_recommend")
    )
    if question is None:
        raise ApiError(500, "SETUP_INCOMPLETE", "تنظیمات اولیه کامل نشده است.")

    already = db.scalar(
        select(Review.id).where(
            Review.user_id == user.id,
            Review.teacher_id == teacher_id,
            Review.course_id.is_(None),
        )
    )
    if already is not None:
        raise ApiError(409, "REVIEW_EXISTS", REVIEW_EXISTS_MESSAGE)

    review = Review(
        teacher_id=teacher_id,
        user_id=user.id,
        overall_rating=body.stars,
        body=text,
        educational_stage=body.reviewer_label,
        status="pending",
    )
    review.answers.append(
        ReviewAnswer(question_id=question.id, value=1 if body.recommends else 0)
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "REVIEW_EXISTS", REVIEW_EXISTS_MESSAGE)

    return ReviewCreatedOut(
        id=review.id,
        status=review.status,
        message="نظر شما پس از بررسی نمایش داده می‌شود.",
    )