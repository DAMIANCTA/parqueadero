from copy import deepcopy
from datetime import datetime, timedelta, UTC

from config import settings


class PaymentRepository:
    INITIAL_SESSIONS = {
        "session-visitor-paid-001": {
            "session_id": "session-visitor-paid-001",
            "plate_text": "VIS1234",
            "qr_code": "QR-VIS1234",
            "entry_time": datetime.now(UTC) - timedelta(hours=2, minutes=10),
            "exit_time": None,
            "session_status": "INSIDE",
            "payment_status": "PAID",
            "cashier_user_id": "cashier-001",
            "amount": 2.25,
            "paid_amount": 2.25,
            "payment_method": "cash",
            "paid_at": datetime.now(UTC) - timedelta(minutes=4),
            "payment_valid_until": datetime.now(UTC) + timedelta(minutes=11),
            "receipt_number": "REC-20260707-0001",
            "notes": "Pago registrado antes de salida",
            "currency": "USD",
        },
        "session-visitor-pending-001": {
            "session_id": "session-visitor-pending-001",
            "plate_text": "VISPEND",
            "qr_code": "QR-VISPEND",
            "entry_time": datetime.now(UTC) - timedelta(minutes=35),
            "exit_time": None,
            "session_status": "INSIDE",
            "payment_status": "PENDING",
            "cashier_user_id": None,
            "amount": None,
            "paid_amount": None,
            "payment_method": None,
            "paid_at": None,
            "payment_valid_until": None,
            "receipt_number": None,
            "notes": None,
            "currency": "USD",
        },
        "session-visitor-done-001": {
            "session_id": "session-visitor-done-001",
            "plate_text": "VISDONE",
            "qr_code": "QR-VISDONE",
            "entry_time": datetime.now(UTC) - timedelta(hours=1, minutes=30),
            "exit_time": datetime.now(UTC) - timedelta(minutes=12),
            "session_status": "OUTSIDE",
            "payment_status": "PAID",
            "cashier_user_id": "cashier-001",
            "amount": 2.25,
            "paid_amount": 2.25,
            "payment_method": "cash",
            "paid_at": datetime.now(UTC) - timedelta(minutes=5),
            "payment_valid_until": datetime.now(UTC) + timedelta(minutes=10),
            "receipt_number": "REC-20260707-0001",
            "notes": "Pago registrado antes de salida",
            "currency": "USD",
        },
    }
    sessions = deepcopy(INITIAL_SESSIONS)

    def find_by_plate(self, plate: str) -> dict | None:
        normalized_plate = plate.strip().upper()
        for session in self.sessions.values():
            if session["plate_text"] == normalized_plate and session["session_status"] == "INSIDE":
                return session.copy()
        return None

    def find_by_qr(self, qr_code: str) -> dict | None:
        for session in self.sessions.values():
            if session["qr_code"] == qr_code and session["session_status"] == "INSIDE":
                return session.copy()
        return None

    def find_by_session_id(self, session_id: str) -> dict | None:
        session = self.sessions.get(session_id)
        return session.copy() if session else None

    def mark_as_paid(self, session_id: str, cashier_user_id: str, amount: float, payment_method: str) -> dict:
        session = self.sessions[session_id]
        return self._apply_paid_state(
            session=session,
            cashier_user_id=cashier_user_id,
            amount=amount,
            payment_method=payment_method,
            notes=session.get("notes"),
        )

    def upsert_session(self, session_id: str, plate_text: str, payment_status: str = "PENDING") -> dict:
        normalized_plate = plate_text.strip().upper()
        existing = self.find_by_plate(normalized_plate)
        if existing is not None:
            session = self.sessions[existing["session_id"]]
            session["session_id"] = session_id
            session["plate_text"] = normalized_plate
            session["session_status"] = "INSIDE"
            session["payment_status"] = payment_status
            if payment_status == "PENDING":
                session["amount"] = None
                session["paid_amount"] = None
                session["payment_method"] = None
                session["paid_at"] = None
                session["payment_valid_until"] = None
                session["receipt_number"] = None
                session["notes"] = None
                session["exit_time"] = None
            elif payment_status == "NOT_REQUIRED":
                session["amount"] = 0.0
                session["paid_amount"] = None
                session["payment_method"] = None
                session["paid_at"] = None
                session["payment_valid_until"] = None
                session["receipt_number"] = None
                session["notes"] = "Monthly permit / member access"
                session["exit_time"] = None
            return session.copy()

        session = {
            "session_id": session_id,
            "plate_text": normalized_plate,
            "qr_code": f"QR-{normalized_plate}",
            "entry_time": datetime.now(UTC),
            "exit_time": None,
            "session_status": "INSIDE",
            "payment_status": payment_status,
            "cashier_user_id": None,
            "amount": None,
            "paid_amount": None,
            "payment_method": None,
            "paid_at": None,
            "payment_valid_until": None,
            "receipt_number": None,
            "notes": None,
            "currency": "USD",
        }
        if payment_status == "NOT_REQUIRED":
            session["amount"] = 0.0
            session["notes"] = "Monthly permit / member access"
        self.sessions[session_id] = session
        return session.copy()

    def mark_as_paid_by_plate(self, plate_text: str, cashier_user_id: str, amount: float, payment_method: str) -> dict | None:
        session = self.find_by_plate(plate_text)
        if session is None:
            return None
        return self.mark_as_paid(
            session_id=session["session_id"],
            cashier_user_id=cashier_user_id,
            amount=amount,
            payment_method=payment_method,
        )

    def register_cash_payment(
        self,
        *,
        session_id: str,
        plate_text: str,
        cashier_user_id: str,
        amount: float,
        payment_method: str,
        notes: str | None,
    ) -> dict | None:
        session = self.sessions.get(session_id)
        if session is None:
            return None

        session["plate_text"] = plate_text.strip().upper()
        return self._apply_paid_state(
            session=session,
            cashier_user_id=cashier_user_id,
            amount=amount,
            payment_method=payment_method,
            notes=notes,
        )

    def close_session(self, *, session_id: str, plate_text: str, payment_status: str, exit_time: datetime) -> dict | None:
        session = self.sessions.get(session_id)
        if session is None:
            return None
        session["plate_text"] = plate_text.strip().upper()
        session["session_status"] = "OUTSIDE"
        session["payment_status"] = payment_status
        session["exit_time"] = exit_time
        return session.copy()

    def generate_receipt_number(self) -> str:
        paid_count = sum(1 for session in self.sessions.values() if session.get("paid_at"))
        sequence = paid_count + 1
        return f"REC-{datetime.now(UTC).strftime('%Y%m%d')}-{sequence:04d}"

    def _apply_paid_state(
        self,
        *,
        session: dict,
        cashier_user_id: str,
        amount: float,
        payment_method: str,
        notes: str | None,
    ) -> dict:
        paid_at = datetime.now(UTC)
        session["session_status"] = "INSIDE"
        session["exit_time"] = None
        session["payment_status"] = "PAID"
        session["cashier_user_id"] = cashier_user_id
        session["amount"] = round(amount, 2)
        session["paid_amount"] = round(amount, 2)
        session["payment_method"] = payment_method
        session["paid_at"] = paid_at
        session["payment_valid_until"] = paid_at + timedelta(minutes=settings.payment_grace_minutes)
        session["receipt_number"] = self.generate_receipt_number()
        session["notes"] = notes.strip() if notes else None
        return session.copy()
