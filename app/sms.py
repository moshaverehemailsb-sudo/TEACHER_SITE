from typing import Protocol

from app.config import sms_provider
from app.errors import ApiError


class SmsError(Exception):
    """ارسال پیامک ناموفق بود."""


class SmsSender(Protocol):
    def send_code(self, phone: str, code: str) -> None: ...


class ConsoleSender:
    """فقط برای توسعه: کد را در ترمینال چاپ می‌کند و پیامکی نمی‌فرستد."""

    def send_code(self, phone: str, code: str) -> None:
        print(f"[SMS-DEV] {phone} -> {code}", flush=True)


def get_sms_sender() -> SmsSender:
    provider = sms_provider()
    if provider == "console":
        return ConsoleSender()
    raise ApiError(503, "SMS_DISABLED", "ارسال پیامک فعال نیست.")