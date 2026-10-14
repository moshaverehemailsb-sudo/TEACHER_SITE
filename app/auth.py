from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import secret_key
from app.deps import get_db
from app.errors import ApiError
from app.models import User

ALGORITHM = "HS256"
TOKEN_TTL = timedelta(days=30)

user_bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    key = secret_key()
    if key is None:
        raise ApiError(503, "AUTH_DISABLED", "ورود کاربر فعال نیست.")
    return key


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(user_bearer),
    db: Session = Depends(get_db),
) -> User:
    secret = _secret()
    if credentials is None:
        raise ApiError(401, "UNAUTHORIZED", "ابتدا وارد شو.")
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise ApiError(401, "UNAUTHORIZED", "نشست نامعتبر است؛ دوباره وارد شو.")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "UNAUTHORIZED", "نشست نامعتبر است؛ دوباره وارد شو.")
    return user