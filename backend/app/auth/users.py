import hmac

from app.auth.models import Role, User


_SAMPLE_USERS: dict[str, dict[str, str]] = {
    "admin": {"password": "admin-pass", "role": Role.ADMIN.value},
    "user": {"password": "user-pass", "role": Role.USER.value},
}


def authenticate_user(username: str, password: str) -> User | None:
    record = _SAMPLE_USERS.get(username)
    if record is None:
        return None

    if not hmac.compare_digest(password, record["password"]):
        return None

    return User(username=username, role=Role(record["role"]))


def get_user(username: str) -> User | None:
    record = _SAMPLE_USERS.get(username)
    if record is None:
        return None
    return User(username=username, role=Role(record["role"]))

