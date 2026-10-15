from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class LoginCode(TimestampMixin, Base):
    __tablename__ = "login_codes"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        Index("ix_login_codes_phone_hash_created_at", "phone_hash", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))