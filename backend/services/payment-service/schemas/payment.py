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
    payment_status: PaymentStatus
    amount_due: float
    currency: str
    cashier_user_id: str | None = None
    payment_method: PaymentMethod | None = None
    paid_at: datetime | None = None


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
