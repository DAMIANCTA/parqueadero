from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


RoleType = Literal["STUDENT", "TEACHER", "STAFF", "DRIVER"]
EntityStatus = Literal["ACTIVE", "INACTIVE"]
PermitStatus = Literal["VALID", "EXPIRED", "SUSPENDED"]
AccessType = Literal["MEMBER", "VISITOR"]


class MemberCreateRequest(BaseModel):
    university_id: str
    document_id: str = Field(min_length=3, max_length=50)
    institutional_id: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=3, max_length=150)
    email: str = Field(min_length=5, max_length=150)
    role_type: RoleType
    status: EntityStatus = "ACTIVE"
    user_id: str | None = None


class MemberResponse(BaseModel):
    id: str
    university_id: str
    document_id: str
    institutional_id: str
    full_name: str
    email: str
    role_type: RoleType
    status: EntityStatus
    created_at: datetime
    updated_at: datetime
    user_id: str | None = None


class MemberListResponse(BaseModel):
    total: int
    items: list[MemberResponse]


class VehicleCreateRequest(BaseModel):
    university_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1, max_length=50)
    status: EntityStatus = "ACTIVE"


class VehicleResponse(BaseModel):
    id: str
    university_id: str
    plate_text: str
    brand: str
    model: str
    color: str
    status: EntityStatus
    created_at: datetime
    updated_at: datetime


class VehicleListResponse(BaseModel):
    total: int
    items: list[VehicleResponse]


class VehicleAuthorizationRequest(BaseModel):
    person_id: str
    is_owner: bool = False
    status: EntityStatus = "ACTIVE"


class VehicleAuthorizationResponse(BaseModel):
    id: str
    university_id: str
    person_id: str
    vehicle_id: str
    is_owner: bool
    status: EntityStatus
    created_at: datetime
    updated_at: datetime


class FaceEnrollMemberRequest(BaseModel):
    face_image_id: str = Field(min_length=1)
    quality_score_hint: float | None = Field(default=None, ge=0, le=1)
    provider_hint: str | None = None


class FaceProfileResponse(BaseModel):
    id: str
    university_id: str
    person_id: str
    face_image_id: str
    template_id: str
    embedding_id: str
    provider: str
    status: EntityStatus
    created_at: datetime
    updated_at: datetime


class FaceProfileListResponse(BaseModel):
    total: int
    items: list[FaceProfileResponse]


class MonthlyPermitCreateRequest(BaseModel):
    university_id: str
    person_id: str
    vehicle_id: str
    start_date: date
    end_date: date
    amount: float = Field(ge=0)
    payment_method: str = Field(min_length=2, max_length=40)
    status: PermitStatus = "VALID"
    paid_at: datetime | None = None
    receipt_number: str | None = None


class MonthlyPermitResponse(BaseModel):
    id: str
    university_id: str
    person_id: str
    vehicle_id: str
    start_date: date
    end_date: date
    amount: float
    payment_method: str
    status: PermitStatus
    paid_at: datetime | None = None
    receipt_number: str | None = None
    created_at: datetime
    updated_at: datetime


class MonthlyPermitListResponse(BaseModel):
    total: int
    items: list[MonthlyPermitResponse]


class PermitLookupResponse(BaseModel):
    found: bool
    plate_text: str | None = None
    permit_status: PermitStatus | None = None
    person_id: str | None = None
    person_name: str | None = None
    role_type: RoleType | None = None
    vehicle_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    message: str


class MemberAccessValidationRequest(BaseModel):
    university_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    face_image_id: str = Field(min_length=1)
    gate_id: str = Field(min_length=1)
    session_person_id: str | None = None


class MemberAccessValidationResponse(BaseModel):
    authorized: bool
    access_type: AccessType = "MEMBER"
    vehicle_registered: bool = False
    person_id: str | None = None
    person_name: str | None = None
    role_type: RoleType | None = None
    vehicle_id: str | None = None
    plate_text: str
    permit_status: PermitStatus | None = None
    face_match: bool = False
    similarity: float = Field(default=0, ge=0, le=1)
    template_id: str | None = None
    provider: str | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)


class VehicleLookupResponse(BaseModel):
    found: bool
    message: str
    vehicle: VehicleResponse | None = None
    authorized_people: list[MemberResponse] = Field(default_factory=list)


class RegisterOwnedVehicleRequest(BaseModel):
    user_id: str
    full_name: str = Field(min_length=3, max_length=150)
    document_number: str | None = None
    phone: str | None = None
    university_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1, max_length=50)
