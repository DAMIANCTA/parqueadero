from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PaymentMethod = Literal["cash", "card", "transfer", "mobile", "online", "other"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED", "CANCELLED", "REFUNDED"]


class SessionPaymentDetail(BaseModel):
    session_id: str
    plate_text: str
    qr_code: str
    entry_time: datetime
    exit_time: datetime | None = None
    session_status: str = "INSIDE"
    payment_status: PaymentStatus
    amount_due: float
    currency: str
    duration_minutes: int | None = None
    cashier_user_id: str | None = None
    payment_method: PaymentMethod | None = None
    paid_at: datetime | None = None
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
    session_id: str
    plate_text: str
    entry_time: datetime
    duration_minutes: int
    amount: float
    currency: str
    payment_status: PaymentStatus


class CashierPaymentRegistrationRequest(BaseModel):
    session_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    cashier_user_id: str = Field(min_length=3, max_length=100)
    notes: str | None = Field(default=None, max_length=500)


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


class PaymentStatusByPlateResponse(BaseModel):
    found: bool
    message: str
    plate_text: str | None = None
    session_id: str | None = None
    payment_status: PaymentStatus | None = None
    amount_due: float | None = None
    paid_at: datetime | None = None


class InternalSessionUpsertRequest(BaseModel):
    session_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    payment_status: PaymentStatus = "PENDING"
