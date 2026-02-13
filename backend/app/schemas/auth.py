from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default='user', pattern='^(admin|user)$')


class UserOut(BaseModel):
    id: int
    username: str
    roles: list[str]
    created_at: datetime

    model_config = {'from_attributes': True}
