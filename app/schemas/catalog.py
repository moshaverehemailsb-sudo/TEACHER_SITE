from pydantic import BaseModel


class SubjectOut(BaseModel):
    key: str
    slug: str


class FilterOptionOut(BaseModel):
    label: str
    subject: str


class FilterGroupOut(BaseModel):
    name: str
    options: list[FilterOptionOut]


class SubjectListOut(BaseModel):
    top: list[str]
    subjects: list[SubjectOut]
    groups: list[FilterGroupOut]