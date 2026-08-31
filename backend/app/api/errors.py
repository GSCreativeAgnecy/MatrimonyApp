from typing import Any

from fastapi import FastAPI, Request
from fastapi import status as http_status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error carrying an error code and HTTP status."""

    code: str = "APP_ERROR"
    status_code: int = http_status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, *, code: str | None = None, extra: dict[str, Any] | None = None) -> None:
        self.message = message
        if code:
            self.code = code
        self.extra = extra or {}
        super().__init__(message)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = http_status.HTTP_404_NOT_FOUND


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status_code = http_status.HTTP_401_UNAUTHORIZED


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = http_status.HTTP_403_FORBIDDEN


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = http_status.HTTP_409_CONFLICT


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = http_status.HTTP_422_UNPROCESSABLE_ENTITY


class RateLimitError(AppError):
    code = "RATE_LIMIT_EXCEEDED"
    status_code = http_status.HTTP_429_TOO_MANY_REQUESTS


def error_response(code: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": {"code": code, "message": message}}
    if extra:
        payload["error"]["details"] = extra
    return payload


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message, exc.extra),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", "invalid value"),
                "type": err.get("type", "value_error"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response("VALIDATION_ERROR", "Request validation failed", {"errors": errors}),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the real error; never leak it to clients.
        import logging

        logging.getLogger("app").exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("INTERNAL_ERROR", "An internal error occurred."),
        )
