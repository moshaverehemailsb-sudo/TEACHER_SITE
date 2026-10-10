from sqlalchemy import Boolean, CheckConstraint, Integer, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_subject", name="uq_users_auth_identity"),
        CheckConstraint(
            "role IN ('student', 'moderator', 'admin')",
            name="role_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(30), nullable=False)
    auth_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="student"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )