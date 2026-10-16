import re
from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

from app.schemas.teachers import CamelModel

REVIEWER_LABELS = [
    "دانش\u200cآموز پایه دهم",
    "دانش\u200cآموز پایه یازدهم",
    "دانش\u200cآموز پایه دوازدهم",
    "فارغ\u200cالتحصیل",
]


def _label_key(text: str) -> str:
    return re.sub(r"[\s\u200c]+", "", text)


_CANONICAL = {_label_key(label): label for label in REVIEWER_LABELS}


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
    reviewer_label: str
    stars: int = Field(ge=1, le=5)
    recommends: bool
    body: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]

    @field_validator("reviewer_label", mode="before")
    @classmethod
    def canonical_label(cls, value):
        if isinstance(value, str):
            label = _CANONICAL.get(_label_key(value))
            if label is not None:
                return label
        raise ValueError("وضعیت تحصیلی نامعتبر است.")


class ReviewCreatedOut(CamelModel):
    id: int
    status: str
    message: str