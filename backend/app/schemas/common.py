from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    detail: str = ""
    request_id: Optional[str] = None
    extra: dict[str, Any] = {}


class MessageOut(BaseModel):
    message: str


class PageOut(BaseModel, Generic[T]):
    items: list[T]
    page: int = 1
    page_size: int = 50
    total: int = 0
