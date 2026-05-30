from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.auth.models import User
from app.core.config import settings


def create_access_token(user: User) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user.username,
        "role": user.role.value,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired access token.") from exc

    subject = payload.get("sub")
    role = payload.get("role")
    if not isinstance(subject, str) or not isinstance(role, str):
        raise ValueError("Invalid access token payload.")

    return {"sub": subject, "role": role}

