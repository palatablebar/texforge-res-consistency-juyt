"""统一业务异常：service 抛出，error_handler 渲染为统一信封。"""
from typing import Any, Optional


class AppError(Exception):
    def __init__(self, code: str, detail: str = "", http_status: int = 400, extra: Optional[dict[str, Any]] = None):
        super().__init__(detail or code)
        self.code = code
        self.detail = detail
        self.http_status = http_status
        self.extra = extra or {}
