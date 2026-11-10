"""解析 Bearer token，注入 request.state.user；401 返回统一错误信封。"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.middlewares.error_handler import build_error
from app.utils.errors import AppError
from app.utils.jwt import decode_access_token

PUBLIC_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc", "/auth/login", "/files/")


def is_public(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def auth_middleware(app):
    @app.middleware("http")
    async def authenticate(request: Request, call_next):
        if request.method == "OPTIONS" or is_public(request.url.path):
            return await call_next(request)
        header = request.headers.get("Authorization", "")
        if not header.lower().startswith("bearer "):
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(status_code=401, content=build_error("TEX-0401", "未登录或 token 缺失", "", request_id))
        token = header.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
            if not payload.get("sub"):
                raise ValueError("missing sub")
        except Exception:  # noqa: BLE001
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(status_code=401, content=build_error("TEX-0401", "登录已过期，请重新登录", "", request_id))
        request.state.user = payload
        return await call_next(request)

    return app


def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise AppError("TEX-0401", "未登录", http_status=401)
    return user


def require_roles(*roles: str):
    """路由依赖：按 workspace_role 限制写操作（owner/editor）。"""

    def dependency(request: Request) -> dict:
        user = get_current_user(request)
        workspace_role = str(user.get("workspace_role", "viewer"))
        if workspace_role not in roles and str(user.get("role")) != "admin":
            raise AppError("TEX-1013", "当前工作区角色无权执行该操作", http_status=403)
        return user

    return dependency
