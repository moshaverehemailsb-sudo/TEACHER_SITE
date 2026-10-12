from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    false,
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
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )

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
    teaching_style: Mapped[str | None] = mapped_column(String(100))
    suitable_level: Mapped[str | None] = mapped_column(String(100))
    normalized_search: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )

    subjects: Mapped[list[Subject]] = relationship(
        secondary=teacher_subjects, back_populates="teachers"
    )
    courses: Mapped[list["Course"]] = relationship(
        secondary=course_teachers, back_populates="teachers"
    )
    detail: Mapped["TeacherBio | None"] = relationship(
        back_populates="teacher", uselist=False, cascade="all, delete-orphan"
    )


class TeacherBio(TimestampMixin, Base):
    __tablename__ = "teacher_bios"

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True
    )
    class_style: Mapped[str | None] = mapped_column(Text)
    method: Mapped[str | None] = mapped_column(Text)
    level_text: Mapped[str | None] = mapped_column(Text)
    problem_solving: Mapped[str | None] = mapped_column(Text)
    education: Mapped[str | None] = mapped_column(Text)
    experience: Mapped[str | None] = mapped_column(String(300))
    note: Mapped[str | None] = mapped_column(Text)

    teacher: Mapped[Teacher] = relationship(back_populates="detail")


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
    course_type: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )

    subject: Mapped[Subject] = relationship(back_populates="courses")
    teachers: Mapped[list[Teacher]] = relationship(
        secondary=course_teachers, back_populates="courses"
    )