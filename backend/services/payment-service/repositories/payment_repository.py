from datetime import datetime, timedelta, UTC


class PaymentRepository:
    sessions = {
        "session-visitor-paid-001": {
            "session_id": "session-visitor-paid-001",
            "plate_text": "VIS1234",
            "qr_code": "QR-VIS1234",
            "entry_time": datetime.now(UTC) - timedelta(hours=2, minutes=10),
            "exit_time": None,
            "payment_status": "PENDING",
            "cashier_user_id": None,
            "amount": None,
            "payment_method": None,
            "paid_at": None,
            "currency": "USD",
        },
        "session-visitor-pending-001": {
            "session_id": "session-visitor-pending-001",
            "plate_text": "VISPEND",
            "qr_code": "QR-VISPEND",
            "entry_time": datetime.now(UTC) - timedelta(minutes=35),
            "exit_time": None,
            "payment_status": "PENDING",
            "cashier_user_id": None,
            "amount": None,
            "payment_method": None,
            "paid_at": None,
            "currency": "USD",
        },
        "session-visitor-done-001": {
            "session_id": "session-visitor-done-001",
            "plate_text": "VISDONE",
            "qr_code": "QR-VISDONE",
            "entry_time": datetime.now(UTC) - timedelta(hours=1, minutes=10),
            "exit_time": None,
            "payment_status": "PAID",
            "cashier_user_id": "cashier-001",
            "amount": 2.25,
            "payment_method": "cash",
            "paid_at": datetime.now(UTC) - timedelta(minutes=5),
            "currency": "USD",
        },
    }

    def find_by_plate(self, plate: str) -> dict | None:
        normalized_plate = plate.strip().upper()
        for session in self.sessions.values():
            if session["plate_text"] == normalized_plate:
                return session.copy()
        return None

    def find_by_qr(self, qr_code: str) -> dict | None:
        for session in self.sessions.values():
            if session["qr_code"] == qr_code:
                return session.copy()
        return None

    def find_by_session_id(self, session_id: str) -> dict | None:
        session = self.sessions.get(session_id)
        return session.copy() if session else None

    def mark_as_paid(self, session_id: str, cashier_user_id: str, amount: float, payment_method: str) -> dict:
        session = self.sessions[session_id]
        session["payment_status"] = "PAID"
        session["cashier_user_id"] = cashier_user_id
        session["amount"] = round(amount, 2)
        session["payment_method"] = payment_method
        session["paid_at"] = datetime.now(UTC)
        return session.copy()
