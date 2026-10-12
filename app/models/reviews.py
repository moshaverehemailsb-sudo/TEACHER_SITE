from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.catalog import Teacher
from app.models.mixins import TimestampMixin
from app.models.users import User


class ReviewQuestion(TimestampMixin, Base):
    __tablename__ = "review_questions"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('rating', 'yes_no')",
            name="question_type_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    question_text: Mapped[str] = mapped_column(String(300), nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )
    display_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "teacher_id"],
            ["course_teachers.course_id", "course_teachers.teacher_id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "overall_rating BETWEEN 1 AND 5",
            name="overall_rating_range",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'hidden')",
            name="status_valid",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR is_imported",
            name="user_or_imported",
        ),
        CheckConstraint("char_length(body) <= 1000", name="body_max_length"),
        Index(
            "uq_reviews_user_teacher_no_course",
            "user_id",
            "teacher_id",
            unique=True,
            postgresql_where=text("course_id IS NULL"),
        ),
        Index(
            "uq_reviews_user_teacher_course",
            "user_id",
            "teacher_id",
            "course_id",
            unique=True,
            postgresql_where=text("course_id IS NOT NULL"),
        ),
        Index("ix_reviews_teacher_id_status", "teacher_id", "status"),
        Index("ix_reviews_course_id_status", "course_id", "status"),
        Index("ix_reviews_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[int | None] = mapped_column(Integer)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    overall_rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    educational_stage: Mapped[str | None] = mapped_column(String(50))
    participated_in_course: Mapped[bool | None] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderation_note: Mapped[str | None] = mapped_column(Text)
    is_imported: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )

    teacher: Mapped[Teacher] = relationship()
    user: Mapped[User | None] = relationship()
    answers: Mapped[list["ReviewAnswer"]] = relationship(
        back_populates="review", cascade="all, delete-orphan", passive_deletes=True
    )


class ReviewAnswer(Base):
    __tablename__ = "review_answers"
    __table_args__ = (
        CheckConstraint("value BETWEEN 0 AND 5", name="value_range"),
        Index("ix_review_answers_question_id", "question_id"),
    )

    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("review_questions.id", ondelete="RESTRICT"), primary_key=True
    )
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    review: Mapped[Review] = relationship(back_populates="answers")
    question: Mapped[ReviewQuestion] = relationship()