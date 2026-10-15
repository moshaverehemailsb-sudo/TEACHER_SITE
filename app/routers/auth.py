from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import TOKEN_TTL, create_access_token, get_current_user
from app.deps import get_db
from app.errors import ApiError
from app.models import User
from app.phone import normalize_phone
from app.ratelimit import code_ip_limiter, verify_ip_limiter
from app.schemas.auth import (
    RequestCodeIn,
    RequestCodeOut,
    TokenOut,
    UserOut,
    VerifyCodeIn,
)
from app.services.otp import (
    CODE_TTL,
    RESEND_INTERVAL,
    ensure_auth_configured,
    request_code,
    verify_code,
)
from app.sms import SmsSender, get_sms_sender

router = APIRouter(prefix="/auth", tags=["auth"])


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def parse_phone(raw: str) -> str:
    phone = normalize_phone(raw)
    if phone is None:
        raise ApiError(422, "INVALID_PHONE", "شماره موبایل معتبر نیست.")
    return phone


@router.post("/request-code", response_model=RequestCodeOut)
def send_code_endpoint(
    body: RequestCodeIn,
    request: Request,
    db: Session = Depends(get_db),
    sender: SmsSender = Depends(get_sms_sender),
):
    ensure_auth_configured()
    code_ip_limiter.check(client_ip(request))
    request_code(db, parse_phone(body.phone), sender)
    return RequestCodeOut(
        message="کد تأیید ارسال شد.",
        expires_in=int(CODE_TTL.total_seconds()),
        retry_after=int(RESEND_INTERVAL.total_seconds()),
    )


@router.post("/verify-code", response_model=TokenOut)
def verify_code_endpoint(
    body: VerifyCodeIn, request: Request, db: Session = Depends(get_db)
):
    ensure_auth_configured()
    verify_ip_limiter.check(client_ip(request))
    user = verify_code(db, parse_phone(body.phone), body.code)
    return TokenOut(
        access_token=create_access_token(user.id),
        expires_in=int(TOKEN_TTL.total_seconds()),
        user=UserOut(id=user.id, display_name=user.display_name),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, display_name=user.display_name)