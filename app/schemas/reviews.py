from datetime import datetime

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