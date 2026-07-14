from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


PaymentMethod = Literal["cash", "card", "transfer", "mobile", "online", "other"]
PaymentStatus = Literal["PENDING", "PAID", "NOT_REQUIRED", "FAILED", "CANCELLED", "REFUNDED"]
AccessType = Literal["VISITOR", "MEMBER"]


class SessionPaymentDetail(BaseModel):
    session_id: str
    plate_text: str
    qr_code: str
    entry_time: datetime
    exit_time: datetime | None = None
    session_status: str = "INSIDE"
    access_type: AccessType = "VISITOR"
    payment_status: PaymentStatus
    amount_due: float
    currency: str
    duration_minutes: int | None = None
    cashier_user_id: str | None = None
    payment_method: PaymentMethod | None = None
    paid_at: datetime | None = None
    paid_amount: float | None = None
    payment_valid_until: datetime | None = None
    receipt_number: str | None = None
    notes: str | None = None


class PaymentSessionResponse(BaseModel):
    found: bool
    message: str
    session: SessionPaymentDetail | None = None


class PaymentRequest(BaseModel):
    session_id: str
    cashier_user_id: str
    payment_method: PaymentMethod
    amount: float = Field(gt=0)


class PaymentByPlateRequest(BaseModel):
    plate_text: str = Field(min_length=3, max_length=20)
    cashier_user_id: str = "cashier-demo"
    payment_method: PaymentMethod = "cash"


class CashierPaymentLookupResponse(BaseModel):
    found: bool
    message: str
    session_id: str | None = None
    plate_text: str | None = None
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    session_status: str | None = None
    access_type: AccessType | None = None
    duration_minutes: int | None = None
    amount: float | None = None
    currency: str | None = None
    payment_status: PaymentStatus | None = None
    paid_at: datetime | None = None
    paid_amount: float | None = None
    payment_method: PaymentMethod | None = None
    payment_valid_until: datetime | None = None
    receipt_number: str | None = None


class CashierPaymentRegistrationRequest(BaseModel):
    session_id: str
    plate_text: str | None = Field(default=None, min_length=3, max_length=20)
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    cashier_user_id: str = Field(min_length=3, max_length=100)
    notes: str | None = Field(default=None, max_length=500, validation_alias=AliasChoices("notes", "observations"))


class CashierPaymentRegistrationResponse(BaseModel):
    success: bool
    message: str
    receipt_number: str | None = None
    paid_at: datetime | None = None
    audit_log_id: str
    session: CashierPaymentLookupResponse | None = None


class PaymentResponse(BaseModel):
    success: bool
    message: str
    session: SessionPaymentDetail | None = None
    audit_log_id: str


class PaymentStatusResponse(BaseModel):
    found: bool
    message: str
    session_id: str | None = None
    payment_status: PaymentStatus | None = None
    amount_due: float | None = None
    paid_at: datetime | None = None
    paid_amount: float | None = None
    payment_valid_until: datetime | None = None
    session_status: str | None = None
    exit_time: datetime | None = None


class PaymentStatusByPlateResponse(BaseModel):
    found: bool
    message: str
    plate_text: str | None = None
    session_id: str | None = None
    access_type: AccessType | None = None
    payment_status: PaymentStatus | None = None
    amount_due: float | None = None
    paid_at: datetime | None = None
    paid_amount: float | None = None
    payment_valid_until: datetime | None = None
    session_status: str | None = None
    exit_time: datetime | None = None


class InternalSessionUpsertRequest(BaseModel):
    session_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    payment_status: PaymentStatus = "PENDING"
    access_type: AccessType = "VISITOR"


class InternalSessionCloseRequest(BaseModel):
    session_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    payment_status: PaymentStatus = "PAID"
    exit_time: datetime
    session_status: str = "OUTSIDE"


class AdminDashboardSummaryResponse(BaseModel):
    active_sessions: int
    vehicles_inside: int
    pending_payments: int
    paid_today: int
    revenue_today: float
    authorized_exits_today: int
    rejected_exits_today: int = 0


class AdminSessionItem(BaseModel):
    session_id: str
    plate_text: str
    entry_time: datetime
    exit_time: datetime | None = None
    duration_minutes: int
    amount: float
    currency: str
    payment_status: PaymentStatus
    session_status: str
    access_type: AccessType = "VISITOR"
    payment_method: PaymentMethod | None = None
    paid_at: datetime | None = None
    paid_amount: float | None = None
    payment_valid_until: datetime | None = None
    receipt_number: str | None = None


class AdminSessionListResponse(BaseModel):
    total: int
    items: list[AdminSessionItem]
