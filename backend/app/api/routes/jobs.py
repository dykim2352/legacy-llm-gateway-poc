from fastapi import APIRouter, Depends, Request

from app.audit.models import AuditEventType
from app.audit.store import append_audit_log
from app.auth.dependencies import require_user_access
from app.auth.models import User
from app.jobs.models import ChatJobCreateResponse, ChatJobRequest, ChatJobStatusResponse
from app.jobs.service import ChatJobService, get_chat_job_service

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/chat", response_model=ChatJobCreateResponse)
async def create_chat_job(
    request: ChatJobRequest,
    http_request: Request,
    current_user: User = Depends(require_user_access),
    service: ChatJobService = Depends(get_chat_job_service),
) -> ChatJobCreateResponse:
    append_audit_log(
        AuditEventType.LLM_REQUEST,
        user=current_user,
        path=str(http_request.url.path),
        success=True,
        message="Async LLM chat job request accepted.",
        metadata={"context_source_count": len(request.context_sources)},
    )
    return await service.create_chat_job(request)


@router.get("/{job_id}", response_model=ChatJobStatusResponse)
def get_chat_job(
    job_id: str,
    current_user: User = Depends(require_user_access),
    service: ChatJobService = Depends(get_chat_job_service),
) -> ChatJobStatusResponse:
    return service.get_chat_job(job_id)
