from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class SellerItem:
    item_id: str
    title: str
    price: str = ""
    url: str = ""


class RequestStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class RequestResult:
    item_id: str
    request_number: int
    status: RequestStatus
    status_code: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class ProgressEvent:
    item_id: str
    completed: int
    total: int
    result: RequestResult
