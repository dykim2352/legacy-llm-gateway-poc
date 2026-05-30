from fastapi import APIRouter, Request, status
from fastapi.exceptions import HTTPException

from app.audit.models import AuditEventType
from app.audit.store import append_audit_log
from app.auth.jwt import create_access_token
from app.auth.models import LoginRequest, LoginResponse
from app.auth.users import authenticate_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request) -> LoginResponse:
    user = authenticate_user(request.username, request.password)
    if user is None:
        append_audit_log(
            AuditEventType.LOGIN_FAILURE,
            username=request.username,
            path=str(http_request.url.path),
            success=False,
            message="Invalid username or password.",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    append_audit_log(
        AuditEventType.LOGIN_SUCCESS,
        user=user,
        path=str(http_request.url.path),
        success=True,
        message="Login succeeded.",
    )
    return LoginResponse(
        access_token=create_access_token(user),
        username=user.username,
        role=user.role,
    )

