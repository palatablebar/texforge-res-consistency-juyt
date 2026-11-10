"""列表分页辅助：统一 page/page_size 语义。"""
from typing import Any


def paginate(items: list[Any], page: int = 1, page_size: int = 50) -> dict:
    page = max(1, page)
    page_size = min(200, max(1, page_size))
    start = (page - 1) * page_size
    return {
        "items": items[start : start + page_size],
        "page": page,
        "page_size": page_size,
        "total": len(items),
    }
