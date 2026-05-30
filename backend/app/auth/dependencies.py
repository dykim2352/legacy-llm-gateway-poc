from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.audit.models import AuditEventType
from app.audit.store import append_audit_log
from app.auth.jwt import decode_access_token
from app.auth.models import Role, User
from app.auth.users import get_user


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        _record_authz_failure(request, None, "Missing bearer token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        _record_authz_failure(request, None, str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = get_user(payload["sub"])
    if user is None:
        message = "Token subject does not match a known user."
        _record_authz_failure(request, payload["sub"], message)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: Role) -> Callable[[Request, User], User]:
    async def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            message = "User does not have permission to access this resource."
            append_audit_log(
                AuditEventType.AUTHZ_FAILURE,
                user=current_user,
                path=str(request.url.path),
                success=False,
                message=message,
                metadata={"allowed_roles": [role.value for role in allowed_roles]},
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
        return current_user

    return dependency


async def require_user_access(current_user: User = Depends(require_roles(Role.USER, Role.ADMIN))) -> User:
    return current_user


async def require_admin_access(current_user: User = Depends(require_roles(Role.ADMIN))) -> User:
    return current_user


def _record_authz_failure(request: Request, username: str | None, message: str) -> None:
    append_audit_log(
        AuditEventType.AUTHZ_FAILURE,
        username=username,
        path=str(request.url.path),
        success=False,
        message=message,
    )

