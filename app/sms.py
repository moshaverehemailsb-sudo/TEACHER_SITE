import logging
from typing import Protocol

import httpx

from app.config import app_env, sms_api_key, sms_provider, sms_sender
from app.errors import ApiError

logger = logging.getLogger("baf.sms")


class SmsError(Exception):
    """ارسال پیامک ناموفق بود."""


class SmsSender(Protocol):
    def send_code(self, phone: str, code: str) -> None: ...


class ConsoleSender:
    """فقط برای توسعه: کد را در ترمینال چاپ می‌کند و پیامکی نمی‌فرستد."""

    def send_code(self, phone: str, code: str) -> None:
        print(f"[SMS-DEV] {phone} -> {code}", flush=True)


class KavenegarSender:
    URL = "https://api.kavenegar.com/v1/{key}/sms/send.json"

    def __init__(self, api_key: str, sender: str):
        self.api_key = api_key
        self.sender = sender

    def send_code(self, phone: str, code: str) -> None:
        message = f"کد ورود شما به باف: {code}"
        try:
            response = httpx.post(
                self.URL.format(key=self.api_key),
                data={"receptor": phone, "sender": self.sender, "message": message},
                timeout=10.0,
            )
            data = response.json()
        except (httpx.HTTPError, ValueError):
            # عمداً جزئیات خطا را نمی‌آوریم: آدرس درخواست شامل کلید API است
            logger.warning("kavenegar request failed (network or invalid response)")
            raise SmsError("kavenegar request failed") from None

        status = data.get("return", {}).get("status") if isinstance(data, dict) else None
        if status != 200:
            logger.warning("kavenegar rejected the request: status=%s", status)
            raise SmsError(f"kavenegar rejected the request: status={status}")


def get_sms_sender() -> SmsSender:
    provider = sms_provider()
    if provider == "console" and app_env() == "development":
        return ConsoleSender()
    if provider == "kavenegar":
        key, sender = sms_api_key(), sms_sender()
        if key and sender:
            return KavenegarSender(key, sender)
    raise ApiError(503, "SMS_DISABLED", "ارسال پیامک فعال نیست.")





