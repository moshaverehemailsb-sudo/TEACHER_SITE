from pydantic import Field, field_validator

from app.phone import to_ascii_digits
from app.schemas.teachers import CamelModel


class RequestCodeIn(CamelModel):
    phone: str = Field(min_length=1, max_length=30)


class RequestCodeOut(CamelModel):
    message: str
    expires_in: int
    retry_after: int


class VerifyCodeIn(CamelModel):
    phone: str = Field(min_length=1, max_length=30)
    code: str = Field(pattern=r"^\d{6}$")

    @field_validator("code", mode="before")
    @classmethod
    def convert_digits(cls, value):
        if isinstance(value, str):
            return to_ascii_digits(value).strip()
        return value


class UserOut(CamelModel):
    id: int
    display_name: str


class TokenOut(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut