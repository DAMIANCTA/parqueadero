from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=100)


class AuthenticatedUserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str | None = None
    role: str
    roles: list[str]
    university_id: str | None = None
    permissions: list[str]
    status: str = "ACTIVE"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    roles: list[str]
    permissions: list[str]
    university_id: str | None = None
    user: AuthenticatedUserResponse


class CurrentUserResponse(AuthenticatedUserResponse):
    sub: str


class UniversityCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    code: str = Field(min_length=2, max_length=20)
    city: str = Field(min_length=2, max_length=120)
    status: str = Field(default="ACTIVE", min_length=3, max_length=20)


class UniversityResponse(BaseModel):
    id: str
    name: str
    code: str
    city: str
    status: str
    created_at: str


class UniversityListResponse(BaseModel):
    total: int
    items: list[UniversityResponse]


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=3, max_length=160)
    email: str | None = Field(default=None, max_length=160)
    role: str = Field(min_length=3, max_length=60)
    university_id: str | None = None
    status: str = Field(default="ACTIVE", min_length=3, max_length=20)


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str | None = None
    role: str
    university_id: str | None = None
    status: str
    created_at: str


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
