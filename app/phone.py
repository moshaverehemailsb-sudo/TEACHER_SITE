import hashlib
import hmac
import re

from app.config import phone_hash_key
from app.errors import ApiError

_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_NOISE = re.compile(r"[\s\-()]")
_MOBILE = re.compile(r"^09\d{9}$")


def to_ascii_digits(text: str) -> str:
    return text.translate(_DIGIT_MAP)


def normalize_phone(raw: str) -> str | None:
    """شماره‌ی موبایل ایران را به شکل 09XXXXXXXXX برمی‌گرداند، یا None اگر نامعتبر باشد."""
    digits = _NOISE.sub("", to_ascii_digits(raw))
    if digits.startswith("+98"):
        digits = "0" + digits[3:]
    elif digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    return digits if _MOBILE.match(digits) else None


def phone_hash(phone: str) -> str:
    key = phone_hash_key()
    if key is None:
        raise ApiError(503, "AUTH_DISABLED", "ورود کاربر فعال نیست.")
    return hmac.new(key.encode(), phone.encode(), hashlib.sha256).hexdigest()