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