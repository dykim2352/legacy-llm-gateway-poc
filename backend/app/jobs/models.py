from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from app.legacy.models import LegacyContextSource


class JobStatus(StrEnum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ChatJobRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=4000,
        validation_alias=AliasChoices("prompt", "message"),
    )
    context: dict[str, Any] = Field(default_factory=dict)
    context_sources: list[LegacyContextSource] = Field(default_factory=list)


class ChatJobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    cache_hit: bool


class ChatJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    cache_hit: bool | None = None
    result: str | None = None
    error: str | None = None
