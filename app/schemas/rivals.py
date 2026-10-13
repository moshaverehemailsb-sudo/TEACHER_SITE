from app.schemas.teachers import CamelModel, TeacherCardOut


class RivalListOut(CamelModel):
    items: list[TeacherCardOut]