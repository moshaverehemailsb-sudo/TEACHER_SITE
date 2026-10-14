from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, StringConstraints

from app.schemas.teachers import CamelModel

Name200 = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Title250 = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)
]
Label100 = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]

CourseStatus = Literal["draft", "published", "archived"]
CourseType = Literal["recorded", "live", "in_person"]


def check_tags(value: list[str]) -> list[str]:
    cleaned = list(dict.fromkeys(t.strip() for t in value if t.strip()))
    if len(cleaned) > 20 or any(len(t) > 100 for t in cleaned):
        raise ValueError("at most 20 tags of up to 100 characters")
    return cleaned


def check_photo_url(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) > 500 or not value.startswith(("assets/", "https://")):
        raise ValueError("photoUrl must start with assets/ or https://")
    return value


Tags = Annotated[list[str], AfterValidator(check_tags)]
PhotoUrl = Annotated[str | None, AfterValidator(check_photo_url)]


# ---------- نظرها ----------
class AdminReviewOut(CamelModel):
    id: int
    teacher_id: int
    teacher_name: str
    reviewer_label: str | None
    stars: int
    recommends: bool | None
    body: str
    status: str
    is_imported: bool
    moderation_note: str | None
    moderated_at: datetime | None
    created_at: datetime


class AdminReviewListOut(CamelModel):
    items: list[AdminReviewOut]
    total: int
    page: int
    page_size: int


class ModerationIn(CamelModel):
    status: Literal["pending", "approved", "rejected", "hidden"]
    note: str | None = Field(default=None, max_length=1000)


# ---------- استادها ----------
class TeacherCreateIn(CamelModel):
    name: Name200
    subjects: list[str] = Field(min_length=1, max_length=5)
    style: str | None = Field(default=None, max_length=100)
    level: str | None = Field(default=None, max_length=100)
    tags: Tags = Field(default_factory=list)
    photo_url: PhotoUrl = None


class TeacherUpdateIn(CamelModel):
    name: Name200 | None = None
    subjects: list[str] | None = Field(default=None, min_length=1, max_length=5)
    style: str | None = Field(default=None, max_length=100)
    level: str | None = Field(default=None, max_length=100)
    tags: Tags | None = None
    photo_url: PhotoUrl = None
    is_active: bool | None = None


class AdminTeacherOut(CamelModel):
    id: int
    slug: str
    name: str
    subjects: list[str]
    style: str | None
    level: str | None
    tags: list[str]
    photo_url: str | None
    is_active: bool


class BioIn(CamelModel):
    class_style: str | None = Field(default=None, max_length=3000)
    method: str | None = Field(default=None, max_length=3000)
    level_text: str | None = Field(default=None, max_length=3000)
    problem_solving: str | None = Field(default=None, max_length=3000)
    education: str | None = Field(default=None, max_length=1000)
    experience: str | None = Field(default=None, max_length=300)
    note: str | None = Field(default=None, max_length=3000)


# ---------- دوره‌ها ----------
class CourseCreateIn(CamelModel):
    title: Title250
    description: str | None = Field(default=None, max_length=3000)
    course_type: CourseType | None = None
    status: CourseStatus = "published"


class CourseUpdateIn(CamelModel):
    title: Title250 | None = None
    description: str | None = Field(default=None, max_length=3000)
    course_type: CourseType | None = None
    status: CourseStatus | None = None
    sort_order: int | None = Field(default=None, ge=0, le=1000)


class AdminCourseOut(CamelModel):
    id: int
    title: str
    description: str | None
    course_type: str | None
    status: str
    sort_order: int
    teacher_ids: list[int]


# ---------- مقایسه‌های پرطرفدار ----------
class PairIn(CamelModel):
    teacher_a_id: int
    teacher_b_id: int
    label: Label100
    sort_order: int | None = Field(default=None, ge=0, le=1000)


class PairOut(CamelModel):
    id: int
    teacher_a_id: int
    teacher_b_id: int
    label: str
    sort_order: int