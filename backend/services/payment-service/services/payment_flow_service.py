from datetime import UTC, datetime

from fastapi import HTTPException

from repositories.audit_log_repository import AuditLogRepository
from repositories.payment_repository import PaymentRepository
from config import settings
from schemas.payment import (
    AdminDashboardSummaryResponse,
    AdminSessionItem,
    AdminSessionListResponse,
    CashierPaymentLookupResponse,
    CashierPaymentRegistrationRequest,
    CashierPaymentRegistrationResponse,
    InternalSessionCloseRequest,
    InternalSessionUpsertRequest,
    PaymentByPlateRequest,
    PaymentRequest,
    PaymentResponse,
    PaymentSessionResponse,
    PaymentStatusByPlateResponse,
    PaymentStatusResponse,
    SessionPaymentDetail,
)
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

    def get_active_payment_by_plate(self, plate_text: str, university_id: str | None = None) -> CashierPaymentLookupResponse:
        session = self.payment_repository.find_active_visitor_session_by_plate(plate_text, university_id=university_id)
        if session is None:
            return CashierPaymentLookupResponse(
                found=False,
                message="No hay una sesion activa para esta placa",
            )
        return self._to_cashier_lookup(session)

    def get_admin_dashboard_summary(self, university_id: str | None = None) -> AdminDashboardSummaryResponse:
        sessions = self._filtered_sessions(university_id)
        today = datetime.now(UTC).date()
        active_sessions = [session for session in sessions if session.get("session_status") == "INSIDE"]
        paid_today_sessions = [
            session
            for session in sessions
            if session.get("paid_at") is not None and session["paid_at"].astimezone(UTC).date() == today
        ]
        authorized_exits = [
            session
            for session in sessions
            if session.get("session_status") == "OUTSIDE"
            and session.get("exit_time") is not None
            and session["exit_time"].astimezone(UTC).date() == today
            and session.get("payment_status") == "PAID"
        ]
        return AdminDashboardSummaryResponse(
            active_sessions=len(active_sessions),
            vehicles_inside=len(active_sessions),
            pending_payments=sum(1 for session in active_sessions if session.get("payment_status") == "PENDING"),
            paid_today=len(paid_today_sessions),
            revenue_today=round(sum(float(session.get("paid_amount") or 0.0) for session in paid_today_sessions), 2),
            authorized_exits_today=len(authorized_exits),
            rejected_exits_today=0,
        )

    def get_admin_active_sessions(self, university_id: str | None = None) -> AdminSessionListResponse:
        sessions = [
            self._to_admin_session_item(session)
            for session in self._filtered_sessions(university_id)
            if session.get("session_status") == "INSIDE"
        ]
        sessions.sort(key=lambda item: item.entry_time, reverse=True)
        return AdminSessionListResponse(total=len(sessions), items=sessions)

    def get_admin_session_history(self, university_id: str | None = None) -> AdminSessionListResponse:
        sessions = [
            self._to_admin_session_item(session)
            for session in self._filtered_sessions(university_id)
            if session.get("session_status") == "OUTSIDE"
        ]
        sessions.sort(key=lambda item: item.exit_time or item.entry_time, reverse=True)
        return AdminSessionListResponse(total=len(sessions), items=sessions)

    def register_cash_payment(self, payload: CashierPaymentRegistrationRequest) -> CashierPaymentRegistrationResponse:
        session = self.payment_repository.find_by_session_id(payload.session_id)
        normalized_plate = payload.plate_text.strip().upper() if payload.plate_text else None
        if session is None:
            audit_log = self.audit_log_repository.create_payment_audit_log(
                action="payment.cashier.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "session_not_found",
                    "plate_text": normalized_plate,
                    "cashier_user_id": payload.cashier_user_id,
                },
            )
            raise HTTPException(status_code=404, detail="No hay una sesion activa para esta placa")

        if normalized_plate and session["plate_text"] != normalized_plate:
            self.audit_log_repository.create_payment_audit_log(
                action="payment.cashier.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "plate_mismatch",
                    "plate_text": normalized_plate,
                    "session_plate_text": session["plate_text"],
                    "cashier_user_id": payload.cashier_user_id,
                },
            )
            raise HTTPException(status_code=409, detail="La sesion activa no corresponde a la placa enviada")

        normalized_plate = session["plate_text"]

        if session.get("session_status") != "INSIDE":
            self.audit_log_repository.create_payment_audit_log(
                action="payment.cashier.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "session_closed",
                    "plate_text": normalized_plate,
                    "cashier_user_id": payload.cashier_user_id,
                    "session_status_before": session.get("session_status"),
                },
            )
            raise HTTPException(status_code=409, detail="La sesion ya fue cerrada")

        if session.get("access_type", "VISITOR") != "VISITOR":
            self.audit_log_repository.create_payment_audit_log(
                action="payment.cashier.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "member_not_required",
                    "plate_text": normalized_plate,
                    "cashier_user_id": payload.cashier_user_id,
                    "access_type": session.get("access_type"),
                    "payment_status_before": session["payment_status"],
                },
            )
            raise HTTPException(status_code=409, detail="Pago no requerido para miembro universitario")

        if session["payment_status"] != "PENDING":
            self.audit_log_repository.create_payment_audit_log(
                action="payment.cashier.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "payment_already_processed",
                    "plate_text": normalized_plate,
                    "cashier_user_id": payload.cashier_user_id,
                    "payment_status_before": session["payment_status"],
                },
            )
            if session["payment_status"] == "PAID":
                raise HTTPException(status_code=409, detail="Pago ya registrado para esta entrada")
            raise HTTPException(status_code=409, detail="Payment can only be registered when payment_status is PENDING")

        amount_due = self.tariff_service.calculate_amount(session["entry_time"])
        if round(payload.amount, 2) != round(amount_due, 2):
            self.audit_log_repository.create_payment_audit_log(
                action="payment.cashier.rejected",
                resource_id=payload.session_id,
                metadata={
                    "reason": "amount_mismatch",
                    "plate_text": normalized_plate,
                    "cashier_user_id": payload.cashier_user_id,
                    "amount_due": amount_due,
                    "amount_received": payload.amount,
                    "payment_status_before": session["payment_status"],
                },
            )
            raise HTTPException(status_code=400, detail="Provided amount does not match the calculated tariff")

        print(
            "payment-service cashier_payment_start "
            f"session_id={payload.session_id} plate_text={normalized_plate} "
            f"payment_status_before={session['payment_status']} session_status_before={session.get('session_status')} "
            f"paid_amount={round(payload.amount, 2)}"
        )
        updated_session = self.payment_repository.register_cash_payment(
            session_id=payload.session_id,
            plate_text=normalized_plate,
            cashier_user_id=payload.cashier_user_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
            notes=payload.notes,
        )
        if updated_session is None:
            raise HTTPException(status_code=404, detail="Active session not found")

        audit_log = self.audit_log_repository.create_payment_audit_log(
            action="payment.cashier.completed",
            resource_id=payload.session_id,
            metadata={
                "plate_text": normalized_plate,
                "cashier_user_id": payload.cashier_user_id,
                "amount": payload.amount,
                "paid_amount": updated_session.get("paid_amount"),
                "payment_method": payload.payment_method,
                "notes": payload.notes,
                "payment_status_before": session["payment_status"],
                "payment_status_after": updated_session.get("payment_status"),
                "session_status_before": session.get("session_status"),
                "session_status_after": updated_session.get("session_status"),
                "paid_at": updated_session.get("paid_at").isoformat() if updated_session.get("paid_at") else None,
                "payment_valid_until": updated_session.get("payment_valid_until").isoformat() if updated_session.get("payment_valid_until") else None,
                "receipt_number": updated_session.get("receipt_number"),
            },
        )
        print(
            "payment-service cashier_payment_completed "
            f"session_id={payload.session_id} plate_text={normalized_plate} "
            f"payment_status_after={updated_session.get('payment_status')} "
            f"paid_at={updated_session.get('paid_at')} "
            f"paid_amount={updated_session.get('paid_amount')} "
            f"payment_valid_until={updated_session.get('payment_valid_until')}"
        )
        return CashierPaymentRegistrationResponse(
            success=True,
            message="Cash payment registered successfully",
            receipt_number=updated_session.get("receipt_number"),
            paid_at=updated_session.get("paid_at"),
            audit_log_id=audit_log["id"],
            session=self._to_cashier_lookup(updated_session),
        )

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

    def pay_session_by_plate(self, payload: PaymentByPlateRequest) -> PaymentResponse:
        session = self.payment_repository.find_by_plate(payload.plate_text)
        if session is None:
            audit_log = self.audit_log_repository.create_payment_audit_log(
                action="payment.pay_by_plate.rejected",
                resource_id=payload.plate_text,
                metadata={"reason": "session_not_found", "plate_text": payload.plate_text},
            )
            return PaymentResponse(
                success=False,
                message="No active session found for the provided plate",
                session=None,
                audit_log_id=audit_log["id"],
            )

        amount_due = self.tariff_service.calculate_amount(session["entry_time"])
        updated_session = self.payment_repository.mark_as_paid_by_plate(
            plate_text=payload.plate_text,
            cashier_user_id=payload.cashier_user_id or settings.demo_cashier_user_id,
            amount=amount_due,
            payment_method=payload.payment_method,
        )
        audit_log = self.audit_log_repository.create_payment_audit_log(
            action="payment.pay_by_plate.completed",
            resource_id=session["session_id"],
            metadata={
                "plate_text": payload.plate_text,
                "cashier_user_id": payload.cashier_user_id,
                "amount": amount_due,
                "payment_method": payload.payment_method,
            },
        )
        return PaymentResponse(
            success=True,
            message="Payment completed successfully for the provided plate",
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

        amount_due = self._effective_amount(session)
        return PaymentStatusResponse(
            found=True,
            message="Payment status retrieved",
            session_id=session["session_id"],
            payment_status=session["payment_status"],
            amount_due=amount_due,
            paid_at=session["paid_at"],
            paid_amount=session.get("paid_amount"),
            payment_valid_until=session.get("payment_valid_until"),
            session_status=session.get("session_status"),
            exit_time=session.get("exit_time"),
        )

    def get_status_by_plate(self, plate_text: str, university_id: str | None = None) -> PaymentStatusByPlateResponse:
        session = self.payment_repository.find_active_visitor_session_by_plate(plate_text, university_id=university_id)
        if session is None:
            return PaymentStatusByPlateResponse(
                found=False,
                message="No hay una sesion activa para esta placa",
            )

        amount_due = self._effective_amount(session)
        return PaymentStatusByPlateResponse(
            found=True,
            message="Payment status retrieved",
            university_id=session.get("university_id"),
            plate_text=session["plate_text"],
            session_id=session["session_id"],
            access_type=session.get("access_type", "VISITOR"),
            payment_status=session["payment_status"],
            amount_due=amount_due,
            paid_at=session["paid_at"],
            paid_amount=session.get("paid_amount"),
            payment_valid_until=session.get("payment_valid_until"),
            session_status=session.get("session_status"),
            exit_time=session.get("exit_time"),
        )

    def upsert_internal_session(self, payload: InternalSessionUpsertRequest) -> SessionPaymentDetail:
        session = self.payment_repository.upsert_session(
            session_id=payload.session_id,
            university_id=payload.university_id,
            plate_text=payload.plate_text,
            payment_status=payload.payment_status,
            access_type=payload.access_type,
        )
        amount_due = self._effective_amount(session)
        return self._to_session_detail(session, amount_due)

    def close_internal_session(self, payload: InternalSessionCloseRequest) -> SessionPaymentDetail:
        session_before = self.payment_repository.find_by_session_id(payload.session_id)
        session = self.payment_repository.close_session(
            session_id=payload.session_id,
            plate_text=payload.plate_text,
            payment_status=payload.payment_status,
            exit_time=payload.exit_time,
        )
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        print(
            "payment-service session_closed "
            f"session_id={payload.session_id} plate_text={payload.plate_text.strip().upper()} "
            f"payment_status_before={session_before.get('payment_status') if session_before else None} "
            f"payment_status_after={session.get('payment_status')} "
            f"session_status_before={session_before.get('session_status') if session_before else None} "
            f"session_status_after={session.get('session_status')} "
            f"paid_at={session.get('paid_at')} paid_amount={session.get('paid_amount')} "
            f"payment_valid_until={session.get('payment_valid_until')} exit_time={session.get('exit_time')}"
        )
        amount_due = self._effective_amount(session)
        return self._to_session_detail(session, amount_due)

    def _session_response(self, session: dict | None, lookup_type: str) -> PaymentSessionResponse:
        if session is None:
            return PaymentSessionResponse(
                found=False,
                message=f"No active session found for {lookup_type}",
                session=None,
            )

        amount_due = self._effective_amount(session)
        return PaymentSessionResponse(
            found=True,
            message="Session retrieved",
            session=self._to_session_detail(session, amount_due),
        )

    def _to_session_detail(self, session: dict, amount_due: float) -> SessionPaymentDetail:
        return SessionPaymentDetail(
            session_id=session["session_id"],
            university_id=session.get("university_id"),
            plate_text=session["plate_text"],
            qr_code=session["qr_code"],
            entry_time=session["entry_time"],
            exit_time=session.get("exit_time"),
            session_status=session.get("session_status", "INSIDE"),
            access_type=session.get("access_type", "VISITOR"),
            payment_status=session["payment_status"],
            amount_due=round(amount_due, 2),
            currency=session["currency"],
            duration_minutes=self._effective_duration_minutes(session),
            cashier_user_id=session.get("cashier_user_id"),
            payment_method=session.get("payment_method"),
            paid_at=session.get("paid_at"),
            paid_amount=session.get("paid_amount"),
            payment_valid_until=session.get("payment_valid_until"),
            receipt_number=session.get("receipt_number"),
            notes=session.get("notes"),
        )

    def _to_cashier_lookup(self, session: dict) -> CashierPaymentLookupResponse:
        is_paid = session.get("payment_status") == "PAID"
        return CashierPaymentLookupResponse(
            found=True,
            message="Pago registrado" if is_paid else "Sesion activa encontrada",
            session_id=session["session_id"],
            university_id=session.get("university_id"),
            plate_text=session["plate_text"],
            entry_time=session["entry_time"],
            exit_time=session.get("exit_time"),
            session_status=session.get("session_status"),
            access_type=session.get("access_type", "VISITOR"),
            duration_minutes=self._effective_duration_minutes(session),
            amount=round(self._effective_amount(session), 2),
            currency=session["currency"],
            payment_status=session["payment_status"],
            paid_at=session.get("paid_at"),
            paid_amount=session.get("paid_amount"),
            payment_method=session.get("payment_method"),
            payment_valid_until=session.get("payment_valid_until"),
            receipt_number=session.get("receipt_number"),
        )

    def _to_admin_session_item(self, session: dict) -> AdminSessionItem:
        return AdminSessionItem(
            session_id=session["session_id"],
            university_id=session.get("university_id"),
            plate_text=session["plate_text"],
            entry_time=session["entry_time"],
            exit_time=session.get("exit_time"),
            duration_minutes=self._effective_duration_minutes(session),
            amount=round(self._effective_amount(session), 2),
            currency=session["currency"],
            payment_status=session["payment_status"],
            session_status=session.get("session_status", "INSIDE"),
            access_type=session.get("access_type", "VISITOR"),
            payment_method=session.get("payment_method"),
            paid_at=session.get("paid_at"),
            paid_amount=session.get("paid_amount"),
            payment_valid_until=session.get("payment_valid_until"),
            receipt_number=session.get("receipt_number"),
        )

    def _effective_amount(self, session: dict) -> float:
        if session.get("payment_status") == "NOT_REQUIRED":
            return 0.0
        if session.get("payment_status") == "PAID" and session.get("paid_amount") is not None:
            return float(session["paid_amount"])
        return self.tariff_service.calculate_amount(session["entry_time"])

    def _effective_duration_minutes(self, session: dict) -> int:
        paid_at = session.get("paid_at")
        if session.get("payment_status") == "PAID" and paid_at is not None:
            return self.tariff_service.calculate_duration_minutes(session["entry_time"], paid_at)
        return self.tariff_service.calculate_duration_minutes(session["entry_time"])

    def _filtered_sessions(self, university_id: str | None = None) -> list[dict]:
        return self.payment_repository.list_all_sessions(university_id)
