import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ORIGINS = "http://localhost:5500,http://127.0.0.1:5500"


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def admin_token() -> str | None:
    token = os.getenv("ADMIN_TOKEN", "").strip()
    return token or None


def secret_key() -> str | None:
    key = os.getenv("SECRET_KEY", "").strip()
    return key or None


def phone_hash_key() -> str | None:
    key = os.getenv("PHONE_HASH_KEY", "").strip()
    return key or None


def sms_provider() -> str:
    return os.getenv("SMS_PROVIDER", "").strip().lower()


def app_env() -> str:
    return os.getenv("APP_ENV", "production").strip().lower()


def frontend_dir() -> str:
    return os.getenv("FRONTEND_DIR", "").strip()


def sms_daily_limit() -> int:
    try:
        return max(1, int(os.getenv("SMS_DAILY_LIMIT", "500")))
    except ValueError:
        return 500


def config_warnings() -> list[str]:
    """مشکلات احتمالی تنظیمات را برمی‌گرداند (برای لاگ هنگام راه‌اندازی)."""
    warnings: list[str] = []
    production = app_env() == "production"

    if secret_key() is None:
        warnings.append("SECRET_KEY is not set: user login is disabled.")
    elif len(secret_key()) < 32:
        warnings.append("SECRET_KEY is shorter than 32 characters.")

    if phone_hash_key() is None:
        warnings.append("PHONE_HASH_KEY is not set: user login is disabled.")

    token = admin_token()
    if token is None:
        warnings.append("ADMIN_TOKEN is not set: the admin API is disabled.")
    elif len(token) < 32:
        warnings.append("ADMIN_TOKEN is shorter than 32 characters.")

    if production and not sms_provider():
        warnings.append("SMS_PROVIDER is not set: SMS codes cannot be sent.")
    if production and sms_provider() == "console":
        warnings.append("SMS_PROVIDER=console does not work in production.")
    return warnings