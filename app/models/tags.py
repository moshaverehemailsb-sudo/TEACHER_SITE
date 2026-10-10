from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.catalog import Teacher
from app.models.mixins import TimestampMixin


class Tag(TimestampMixin, Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class TeacherTag(TimestampMixin, Base):
    __tablename__ = "teacher_tags"
    __table_args__ = (
        CheckConstraint(
            "source IN ('verified', 'student_reported', 'ai_inferred')",
            name="source_valid",
        ),
        Index("ix_teacher_tags_tag_id", "tag_id"),
    )

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    source: Mapped[str] = mapped_column(String(20), primary_key=True)

    teacher: Mapped[Teacher] = relationship()
    tag: Mapped[Tag] = relationship()
    