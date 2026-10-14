from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def find_or_create_user(
    db: Session, provider: str, subject: str, display_name: str
) -> User:
    """کاربر را با (روش ورود، شناسه) پیدا می‌کند یا می‌سازد. commit با فراخواننده است."""
    user = db.scalar(
        select(User).where(
            User.auth_provider == provider, User.auth_subject == subject
        )
    )
    if user is None:
        user = User(
            auth_provider=provider,
            auth_subject=subject,
            display_name=(display_name.strip() or "کاربر")[:100],
        )
        db.add(user)
        db.flush()
    return user