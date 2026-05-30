from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(BaseModel):
    username: str
    role: Role


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: Role

