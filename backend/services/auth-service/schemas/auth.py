from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    roles: list[str]
    permissions: list[str]
    university_id: str | None = None


class CurrentUserResponse(BaseModel):
    sub: str
    username: str
    roles: list[str]
    permissions: list[str]
    university_id: str | None = None
