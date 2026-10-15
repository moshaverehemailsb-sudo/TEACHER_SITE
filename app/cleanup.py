from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import LoginCode

KEEP = timedelta(days=1)


def delete_old_codes(db: Session) -> int:
    """کدهای ورود قدیمی‌تر از یک روز را پاک می‌کند و تعدادشان را برمی‌گرداند."""
    cutoff = datetime.now(timezone.utc) - KEEP
    result = db.execute(delete(LoginCode).where(LoginCode.created_at < cutoff))
    return result.rowcount


def main() -> None:
    with SessionLocal() as db:
        count = delete_old_codes(db)
        db.commit()
    print("deleted login codes =", count)


if __name__ == "__main__":
    main()