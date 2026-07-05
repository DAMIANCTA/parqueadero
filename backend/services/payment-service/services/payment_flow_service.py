from repositories.audit_log_repository import AuditLogRepository
from repositories.payment_repository import PaymentRepository
from schemas.payment import PaymentRequest, PaymentResponse, PaymentSessionResponse, PaymentStatusResponse, SessionPaymentDetail
from services.tariff_service import TariffService


class PaymentFlowService:
    def __init__(self) -> None:
        self.payment_repository = PaymentRepository()
        self.tariff_service = TariffService()
        self.audit_log_repository = AuditLogRepository()

    def get_session_by_plate(self, plate: str) -> PaymentSessionResponse:
        session = self.payment_repository.find_by_plate(plate)
        return self._session_response(session, "plate")

    def get_session_by_qr(self, qr_code: str) -> PaymentSessionResponse:
        session = self.payment_repository.find_by_qr(qr_code)
        return self._session_response(session, "qr")

    def pay_session(self, payload: PaymentRequest) -> PaymentResponse:
        session = self.payment_repository.find_by_session_id(payload.session_id)
        if session is None:
            audit_log = self.audit_log_repository.create_payment_audit_log(
                action="payment.pay.rejected",
                resource_id=payload.session_id,
                metadata={"reason": "session_not_found", "cashier_user_id": payload.cashier_user_id},
            )
            return PaymentResponse(
                success=False,
                message="Session not found",
                session=None,
                audit_log_id=audit_log["id"],
            )

        amount_due = self.tariff_service.calculate_amount(session["entry_time"])
        if round(payload.amount, 2) < round(amount_due, 2):
            audit_log = self.audit_log_repository.create_payment_audit_log(
                action="payment.pay.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "insufficient_amount",
                    "cashier_user_id": payload.cashier_user_id,
                    "amount_due": amount_due,
                    "amount_received": payload.amount,
                },
            )
            return PaymentResponse(
                success=False,
                message="Amount is lower than the calculated tariff",
                session=self._to_session_detail(session, amount_due),
                audit_log_id=audit_log["id"],
            )

        updated_session = self.payment_repository.mark_as_paid(
            session_id=payload.session_id,
            cashier_user_id=payload.cashier_user_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
        )
        audit_log = self.audit_log_repository.create_payment_audit_log(
            action="payment.pay.completed",
            resource_id=payload.session_id,
            metadata={
                "cashier_user_id": payload.cashier_user_id,
                "amount": payload.amount,
                "payment_method": payload.payment_method,
            },
        )
        return PaymentResponse(
            success=True,
            message="Payment completed successfully",
            session=self._to_session_detail(updated_session, amount_due),
            audit_log_id=audit_log["id"],
        )

    def get_status(self, session_id: str) -> PaymentStatusResponse:
        session = self.payment_repository.find_by_session_id(session_id)
        if session is None:
            return PaymentStatusResponse(
                found=False,
                message="Session not found",
            )

        amount_due = self.tariff_service.calculate_amount(session["entry_time"])
        return PaymentStatusResponse(
            found=True,
            message="Payment status retrieved",
            session_id=session["session_id"],
            payment_status=session["payment_status"],
            amount_due=amount_due,
            paid_at=session["paid_at"],
        )

    def _session_response(self, session: dict | None, lookup_type: str) -> PaymentSessionResponse:
        if session is None:
            return PaymentSessionResponse(
                found=False,
                message=f"No active session found for {lookup_type}",
                session=None,
            )

        amount_due = self.tariff_service.calculate_amount(session["entry_time"])
        return PaymentSessionResponse(
            found=True,
            message="Session retrieved",
            session=self._to_session_detail(session, amount_due),
        )

    def _to_session_detail(self, session: dict, amount_due: float) -> SessionPaymentDetail:
        return SessionPaymentDetail(
            session_id=session["session_id"],
            plate_text=session["plate_text"],
            qr_code=session["qr_code"],
            entry_time=session["entry_time"],
            exit_time=session.get("exit_time"),
            payment_status=session["payment_status"],
            amount_due=round(amount_due, 2),
            currency=session["currency"],
            cashier_user_id=session.get("cashier_user_id"),
            payment_method=session.get("payment_method"),
            paid_at=session.get("paid_at"),
        )
