from fastapi import APIRouter, Depends

from app.audit.models import AuditLogEntry
from app.audit.store import list_audit_logs
from app.auth.dependencies import require_admin_access
from app.auth.models import User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/audit-logs", response_model=list[AuditLogEntry])
async def get_audit_logs(
    current_user: User = Depends(require_admin_access),
) -> list[AuditLogEntry]:
    return list_audit_logs()

