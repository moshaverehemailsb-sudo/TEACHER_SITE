from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.catalog import Subject, Teacher
from app.models.mixins import TimestampMixin


class SubjectGroup(TimestampMixin, Base):
    __tablename__ = "subject_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )

    options: Mapped[list["SubjectFilterOption"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="SubjectFilterOption.sort_order",
    )


class SubjectFilterOption(TimestampMixin, Base):
    __tablename__ = "subject_filter_options"
    __table_args__ = (
        UniqueConstraint(
            "group_id", "label", name="uq_subject_filter_options_group_label"
        ),
        Index("ix_subject_filter_options_subject_id", "subject_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("subject_groups.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )

    group: Mapped[SubjectGroup] = relationship(back_populates="options")
    subject: Mapped[Subject] = relationship()


class PopularComparison(TimestampMixin, Base):
    __tablename__ = "popular_comparisons"
    __table_args__ = (
        CheckConstraint("teacher_a_id <> teacher_b_id", name="different_teachers"),
        UniqueConstraint(
            "teacher_a_id", "teacher_b_id", name="uq_popular_comparisons_pair"
        ),
        Index("ix_popular_comparisons_teacher_b_id", "teacher_b_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_a_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    teacher_b_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )

    teacher_a: Mapped[Teacher] = relationship(foreign_keys=[teacher_a_id])
    teacher_b: Mapped[Teacher] = relationship(foreign_keys=[teacher_b_id])