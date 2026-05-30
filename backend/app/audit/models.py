from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(StrEnum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    AUTHZ_FAILURE = "AUTHZ_FAILURE"
    LLM_REQUEST = "LLM_REQUEST"
    LEGACY_LOOKUP = "LEGACY_LOOKUP"


class AuditLogEntry(BaseModel):
    id: int
    timestamp: datetime
    event_type: AuditEventType
    username: str | None = None
    role: str | None = None
    path: str | None = None
    success: bool
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

