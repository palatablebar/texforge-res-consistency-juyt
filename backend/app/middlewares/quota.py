"""Redis 滑动窗口限流 + 配方级生成互斥（锁在 service 内获取）。"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.middlewares.error_handler import build_error
from app.utils.cache import sliding_window_hit
from app.utils.logger import log_event

LIMITS = {
    ("POST", "/generate"): 20,
    ("POST", "/packs"): 15,
}
WINDOW_SECONDS = 60


def quota_middleware(app):
    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)
        path = request.url.path
        limit = None
        for (method, suffix), value in LIMITS.items():
            if method == request.method and path.endswith(suffix):
                limit = value
                break
        if limit is None:
            return await call_next(request)
        user = getattr(request.state, "user", None) or {}
        user_id = user.get("sub", "anonymous")
        key = f"rl:texforge:{user_id}:{path}"
        allowed, retry_after = sliding_window_hit(key, limit, WINDOW_SECONDS)
        if not allowed:
            request_id = getattr(request.state, "request_id", None)
            log_event("RATE_LIMIT_HIT", user_id=user_id, route=path, retry_after=retry_after)
            response = JSONResponse(
                status_code=429,
                content=build_error("TEX-1010", "请求过于频繁，请稍后再试", f"retry_after={retry_after}", request_id,
                                    {"retry_after": retry_after}),
            )
            response.headers["Retry-After"] = str(retry_after)
            return response
        return await call_next(request)

    return app
