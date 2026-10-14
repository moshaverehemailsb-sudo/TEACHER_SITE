from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from app.schemas.teachers import CamelModel


class ReviewOut(CamelModel):
    id: int
    reviewer_label: str | None
    stars: int
    recommends: bool | None
    body: str
    created_at: datetime


class ReviewListOut(CamelModel):
    items: list[ReviewOut]
    total: int
    page: int
    page_size: int


class ReviewIn(CamelModel):
    reviewer_label: Literal[
        "دانش‌آموز پایه دهم",
        "دانش‌آموز پایه یازدهم",
        "دانش‌آموز پایه دوازدهم",
        "فارغ‌التحصیل",
    ]
    stars: int = Field(ge=1, le=5)
    recommends: bool
    body: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]


class ReviewCreatedOut(CamelModel):
    id: int
    status: str
    message: str