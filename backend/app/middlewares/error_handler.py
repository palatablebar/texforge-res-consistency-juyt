"""统一错误信封 + request_id：{code, message, detail, request_id}。"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.constants.error_codes import ERROR_MESSAGES
from app.utils.errors import AppError
from app.utils.logger import log_event


def request_id_middleware_factory(app):
    import uuid

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        request.state.error_context = {}
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    return app


def build_error(code: str, message: str, detail: str, request_id: str | None, extra: dict | None = None) -> dict:
    return {"code": code, "message": message, "detail": detail, "request_id": request_id, "extra": extra or {}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    message = ERROR_MESSAGES.get(exc.code, exc.detail or exc.code)
    log_event("RATE_LIMIT_HIT" if exc.http_status == 429 else "GENERATION_FAILED",
              user_id=(getattr(request.state, "user", {}) or {}).get("sub"),
              route=request.url.path, error=exc.code)
    return JSONResponse(
        status_code=exc.http_status,
        content=build_error(exc.code, message, exc.detail, request_id, exc.extra),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    log_event("GENERATION_FAILED", recipe_id=None, variant_id=None, error=f"unhandled:{exc}")
    return JSONResponse(
        status_code=500,
        content=build_error("TEX-1500", "服务器内部错误", str(exc), request_id),
    )
