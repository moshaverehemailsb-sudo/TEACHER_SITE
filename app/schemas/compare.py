from app.schemas.teachers import CamelModel, TeacherCardOut


class CompareTeacherOut(TeacherCardOut):
    education: str | None
    experience: str | None


class CompareOut(CamelModel):
    subject: str
    a: CompareTeacherOut
    b: CompareTeacherOut


class PopularComparisonOut(CamelModel):
    id: int
    label: str
    a: TeacherCardOut
    b: TeacherCardOut


class PopularComparisonListOut(CamelModel):
    items: list[PopularComparisonOut]