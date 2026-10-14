from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    error: dict = {"code": code, "message": message}
    if details:
        error["details"] = details
    return JSONResponse(
        status_code=status_code, content={"error": error}, headers=headers
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return error_response(
        422, "VALIDATION_ERROR", "داده‌های ارسالی معتبر نیستند.", details
    )


HTTP_ERRORS = {
    404: ("NOT_FOUND", "آدرس پیدا نشد."),
    405: ("METHOD_NOT_ALLOWED", "این متد برای این آدرس مجاز نیست."),
}


async def http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code, message = HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", str(exc.detail)))
    return error_response(
        exc.status_code, code, message, headers=getattr(exc, "headers", None)
    )