from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.audit.models import AuditEventType
from app.audit.store import append_audit_log
from app.auth.dependencies import require_user_access
from app.auth.models import User
from app.legacy.client import LegacyContextClient, get_legacy_context_client
from app.legacy.models import LegacyContextSource, LegacySourceType

router = APIRouter(prefix="/api/v1/legacy", tags=["legacy"])


@router.get("/erp/orders/{order_id}")
async def get_erp_order(
    order_id: str,
    request: Request,
    current_user: User = Depends(require_user_access),
    legacy_client: LegacyContextClient = Depends(get_legacy_context_client),
) -> dict[str, Any]:
    return await _fetch_required_source(
        LegacyContextSource(type=LegacySourceType.ERP_ORDER, id=order_id),
        request,
        current_user,
        legacy_client,
    )


@router.get("/pdm/parts/{part_id}")
async def get_pdm_part(
    part_id: str,
    request: Request,
    current_user: User = Depends(require_user_access),
    legacy_client: LegacyContextClient = Depends(get_legacy_context_client),
) -> dict[str, Any]:
    return await _fetch_required_source(
        LegacyContextSource(type=LegacySourceType.PDM_PART, id=part_id),
        request,
        current_user,
        legacy_client,
    )


@router.get("/groupware/users/{user_id}")
async def get_groupware_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_user_access),
    legacy_client: LegacyContextClient = Depends(get_legacy_context_client),
) -> dict[str, Any]:
    return await _fetch_required_source(
        LegacyContextSource(type=LegacySourceType.GROUPWARE_USER, id=user_id),
        request,
        current_user,
        legacy_client,
    )


async def _fetch_required_source(
    source: LegacyContextSource,
    request: Request,
    current_user: User,
    legacy_client: LegacyContextClient,
) -> dict[str, Any]:
    data, warning = await legacy_client.fetch_source(source)
    success = data is not None
    append_audit_log(
        AuditEventType.LEGACY_LOOKUP,
        user=current_user,
        path=str(request.url.path),
        success=success,
        message="Legacy lookup succeeded." if success else warning or "Legacy lookup failed.",
        metadata={"source_type": source.type.value, "source_id": source.id},
    )

    if data is not None:
        return data

    detail = warning or f"{source.type.value} {source.id} lookup failed"
    if "not found" in detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

