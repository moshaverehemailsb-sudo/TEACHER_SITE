import secrets

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import admin_token
from app.errors import ApiError

bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    expected = admin_token()
    if expected is None:
        raise ApiError(503, "ADMIN_DISABLED", "بخش مدیریت فعال نیست.")
    token = credentials.credentials if credentials else ""
    if not secrets.compare_digest(token.encode(), expected.encode()):
        raise ApiError(401, "UNAUTHORIZED", "دسترسی مجاز نیست.")