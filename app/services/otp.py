import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import phone_hash_key, secret_key, sms_daily_limit
from app.errors import ApiError
from app.models import LoginCode, User
from app.phone import phone_hash
from app.services.users import find_or_create_user
from app.sms import SmsError, SmsSender

CODE_TTL = timedelta(minutes=2)
RESEND_INTERVAL = timedelta(seconds=60)
MAX_CODES_PER_HOUR = 5
MAX_ATTEMPTS = 5

INVALID_CODE = ("CODE_INVALID", "کد نامعتبر یا منقضی شده است.")


def ensure_auth_configured() -> None:
    if secret_key() is None or phone_hash_key() is None:
        raise ApiError(503, "AUTH_DISABLED", "ورود کاربر فعال نیست.")


def _code_hash(phone_digest: str, code: str) -> str:
    key = (phone_hash_key() or "").encode()
    return hmac.new(key, f"{phone_digest}:{code}".encode(), hashlib.sha256).hexdigest()


def request_code(db: Session, phone: str, sender: SmsSender) -> None:
    digest = phone_hash(phone)
    now = datetime.now(timezone.utc)

    last = db.scalar(
        select(LoginCode)
        .where(LoginCode.phone_hash == digest)
        .order_by(LoginCode.created_at.desc())
        .limit(1)
    )
    if last is not None and now - last.created_at < RESEND_INTERVAL:
        raise ApiError(
            429,
            "CODE_RECENTLY_SENT",
            "کد تأیید به‌تازگی ارسال شده؛ کمی بعد دوباره تلاش کن.",
        )

    recent = db.scalar(
        select(func.count())
        .select_from(LoginCode)
        .where(
            LoginCode.phone_hash == digest,
            LoginCode.created_at > now - timedelta(hours=1),
        )
    )
    if recent >= MAX_CODES_PER_HOUR:
        raise ApiError(
            429, "RATE_LIMITED", "تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کن."
        )

    # سقف کلی کل سایت در ۲۴ ساعت، برای جلوگیری از خرج شدن اعتبار پیامک
    daily = db.scalar(
        select(func.count())
        .select_from(LoginCode)
        .where(LoginCode.created_at > now - timedelta(hours=24))
    )
    if daily >= sms_daily_limit():
        raise ApiError(
            503,
            "SMS_LIMIT_REACHED",
            "سقف ارسال پیامک امروز پر شده؛ فردا دوباره تلاش کن.",
        )

    code = f"{secrets.randbelow(1_000_000):06d}"
    row = LoginCode(
        phone_hash=digest,
        code_hash=_code_hash(digest, code),
        expires_at=now + CODE_TTL,
    )
    db.add(row)
    db.commit()

    try:
        sender.send_code(phone, code)
    except SmsError:
        db.delete(row)
        db.commit()
        raise ApiError(
            502, "SMS_FAILED", "ارسال پیامک ممکن نشد؛ کمی بعد دوباره تلاش کن."
        )


def verify_code(db: Session, phone: str, code: str) -> User:
    digest = phone_hash(phone)
    now = datetime.now(timezone.utc)

    row = db.scalar(
        select(LoginCode)
        .where(
            LoginCode.phone_hash == digest,
            LoginCode.consumed_at.is_(None),
            LoginCode.expires_at > now,
        )
        .order_by(LoginCode.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    if row is None:
        raise ApiError(400, *INVALID_CODE)
    if row.attempts >= MAX_ATTEMPTS:
        raise ApiError(
            429, "TOO_MANY_ATTEMPTS", "تعداد تلاش‌ها زیاد است؛ یک کد جدید بگیر."
        )

    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, _code_hash(digest, code)):
        db.commit()
        raise ApiError(400, *INVALID_CODE)

    row.consumed_at = now
    user = find_or_create_user(db, "phone", digest, "کاربر")
    if not user.is_active:
        db.commit()
        raise ApiError(403, "ACCOUNT_DISABLED", "این حساب غیرفعال شده است.")
    db.commit()
    return user