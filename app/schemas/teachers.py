from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TeacherCardOut(CamelModel):
    id: int
    name: str
    subject: str | None
    style: str | None
    level: str | None
    tags: list[str]
    photo_url: str | None
    rating: float | None
    review_count: int
    recommend_percent: int | None


class TeacherListOut(CamelModel):
    items: list[TeacherCardOut]
    total: int
    page: int
    page_size: int