from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin

teacher_subjects = Table(
    "teacher_subjects",
    Base.metadata,
    Column("teacher_id", ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_teacher_subjects_subject_id", "subject_id"),
)

course_teachers = Table(
    "course_teachers",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("teacher_id", ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_course_teachers_teacher_id", "teacher_id"),
)


class Subject(TimestampMixin, Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    teachers: Mapped[list["Teacher"]] = relationship(
        secondary=teacher_subjects, back_populates="subjects"
    )
    courses: Mapped[list["Course"]] = relationship(back_populates="subject")


class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500))
    short_description: Mapped[str | None] = mapped_column(String(300))
    bio: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )

    subjects: Mapped[list[Subject]] = relationship(
        secondary=teacher_subjects, back_populates="teachers"
    )
    courses: Mapped[list["Course"]] = relationship(
        secondary=course_teachers, back_populates="teachers"
    )


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "course_type IN ('recorded', 'live', 'in_person')",
            name="course_type_valid",
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )

    subject: Mapped[Subject] = relationship(back_populates="courses")
    teachers: Mapped[list[Teacher]] = relationship(
        secondary=course_teachers, back_populates="courses"
    )