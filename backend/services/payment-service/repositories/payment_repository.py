import logging
from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any
from uuid import UUID

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)


def _app_session_status(db_status: str) -> str:
    return "INSIDE" if db_status == "open" else "OUTSIDE"


def _app_access_type(session_type: str) -> str:
    return "MEMBER" if session_type == "internal" else "VISITOR"


_DEMO_PAID_SESSION_ID = "66666666-6666-6666-6666-666666666601"


class PaymentRepository:
    UCE_ID = "11111111-1111-1111-1111-111111111111"

    def __init__(self) -> None:
        self._ensure_seed_payment()

    def _ensure_seed_payment(self) -> None:
        # Espeja la sesion demo VIS1234 que parking-service ya siembra como
        # "adentro" - aqui se le agrega un pago ya registrado, igual que el
        # mock traia precargado, para que la demo de caja siga siendo util.
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT id, university_id FROM parking_sessions WHERE id = %(id)s",
                    {"id": UUID(_DEMO_PAID_SESSION_ID)},
                )
                session_row = cursor.fetchone()
                if session_row is None:
                    return
                cursor.execute(
                    "SELECT 1 FROM payments WHERE parking_session_id = %(id)s",
                    {"id": session_row["id"]},
                )
                if cursor.fetchone() is not None:
                    return
                cursor.execute(
                    """
                    INSERT INTO payments (
                        id, university_id, parking_session_id, reference_code,
                        amount, currency, payment_method, payment_status, paid_at, notes
                    )
                    VALUES (
                        gen_random_uuid(), %(university_id)s, %(session_id)s, 'REC-DEMO-0001',
                        2.25, 'USD', 'cash', 'paid', NOW() - INTERVAL '4 minutes', 'Pago registrado antes de salida'
                    )
                    """,
                    {"university_id": session_row["university_id"], "session_id": session_row["id"]},
                )
            connection.commit()

    def find_by_plate(self, plate: str, university_id: str | None = None) -> dict | None:
        return self.find_active_visitor_session_by_plate(plate, university_id=university_id)

    def find_active_visitor_session_by_plate(self, plate: str, university_id: str | None = None) -> dict | None:
        normalized_plate = plate.strip().upper()
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                session_row = self._select_session(
                    cursor,
                    plate=normalized_plate,
                    university_id=university_id,
                    require_open=True,
                    require_visitor=True,
                )
                if session_row is None:
                    return None
                payment_row = self._latest_payment(cursor, session_row["id"])
        return self._to_shadow_dict(session_row, payment_row)

    def find_by_qr(self, qr_code: str) -> dict | None:
        plate = qr_code[3:] if qr_code.upper().startswith("QR-") else qr_code
        return self.find_active_visitor_session_by_plate(plate)

    def find_by_session_id(self, session_id: str) -> dict | None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                session_row = self._select_session(cursor, session_id=session_id)
                if session_row is None:
                    return None
                payment_row = self._latest_payment(cursor, session_row["id"])
        return self._to_shadow_dict(session_row, payment_row)

    def mark_as_paid(self, session_id: str, cashier_user_id: str, amount: float, payment_method: str) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                session_row = self._select_session(cursor, session_id=session_id)
                payment_row = self._upsert_payment(
                    cursor,
                    session_row=session_row,
                    payment_status="paid",
                    amount=amount,
                    payment_method=payment_method,
                    cashier_user_id=cashier_user_id,
                    notes=None,
                    set_paid_at=True,
                )
            connection.commit()
        return self._to_shadow_dict(session_row, payment_row)

    def upsert_session(
        self,
        session_id: str,
        university_id: str | None,
        plate_text: str,
        payment_status: str = "PENDING",
        access_type: str = "VISITOR",
    ) -> dict:
        # parking-service ya creo/actualizo la fila real en parking_sessions
        # antes de llamar aqui; esto solo se encarga de dejar un registro de
        # pago inicial cuando el acceso no requiere cobro (miembro
        # universitario), para que las consultas de pago tengan algo que leer.
        del access_type
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                session_row = self._select_session(cursor, session_id=session_id)
                payment_row = None
                if session_row is not None and payment_status.upper() == "NOT_REQUIRED":
                    payment_row = self._upsert_payment(
                        cursor,
                        session_row=session_row,
                        payment_status="not_required",
                        amount=0.0,
                        payment_method=None,
                        cashier_user_id=None,
                        notes="Monthly permit / member access",
                        set_paid_at=False,
                    )
                elif session_row is not None:
                    payment_row = self._latest_payment(cursor, session_row["id"])
            connection.commit()
        if session_row is None:
            return {
                "session_id": session_id,
                "university_id": university_id or self.UCE_ID,
                "plate_text": plate_text.strip().upper(),
                "qr_code": f"QR-{plate_text.strip().upper()}",
                "entry_time": datetime.now(UTC),
                "exit_time": None,
                "session_status": "INSIDE",
                "access_type": "VISITOR",
                "payment_status": payment_status,
                "cashier_user_id": None,
                "amount": 0.0 if payment_status.upper() == "NOT_REQUIRED" else None,
                "paid_amount": None,
                "payment_method": None,
                "paid_at": None,
                "payment_valid_until": None,
                "receipt_number": None,
                "notes": None,
                "currency": "USD",
            }
        return self._to_shadow_dict(session_row, payment_row)

    def mark_as_paid_by_plate(
        self,
        plate_text: str,
        cashier_user_id: str,
        amount: float,
        payment_method: str,
        university_id: str | None = None,
    ) -> dict | None:
        session = self.find_active_visitor_session_by_plate(plate_text, university_id=university_id)
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
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                session_row = self._select_session(cursor, session_id=session_id)
                if session_row is None:
                    return None
                payment_row = self._upsert_payment(
                    cursor,
                    session_row=session_row,
                    payment_status="paid",
                    amount=amount,
                    payment_method=payment_method,
                    cashier_user_id=cashier_user_id,
                    notes=notes,
                    set_paid_at=True,
                )
            connection.commit()
        return self._to_shadow_dict(session_row, payment_row)

    def close_session(self, *, session_id: str, plate_text: str, payment_status: str, exit_time: datetime) -> dict | None:
        del plate_text  # parking-service ya cerro la sesion real; solo leemos su estado
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                session_row = self._select_session(cursor, session_id=session_id)
                if session_row is None:
                    return None
                payment_row = self._latest_payment(cursor, session_row["id"])
        return self._to_shadow_dict(session_row, payment_row)

    def list_all_sessions(self, university_id: str | None = None) -> list[dict]:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                clause = "WHERE university_id = %(university_id)s" if university_id else ""
                params = {"university_id": UUID(university_id)} if university_id else {}
                cursor.execute(
                    f"SELECT * FROM parking_sessions {clause} ORDER BY entry_time DESC",
                    params,
                )
                session_rows = cursor.fetchall()
                results = []
                for session_row in session_rows:
                    payment_row = self._latest_payment(cursor, session_row["id"])
                    results.append(self._to_shadow_dict(session_row, payment_row))
        return results

    def generate_receipt_number(self) -> str:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT nextval('payments_receipt_seq') AS seq")
                seq = cursor.fetchone()["seq"]
        return f"REC-{datetime.now(UTC):%Y%m%d}-{seq:04d}"

    # ------------------------------------------------------------------ #
    def _select_session(
        self,
        cursor,
        *,
        session_id: str | None = None,
        plate: str | None = None,
        university_id: str | None = None,
        require_open: bool = False,
        require_visitor: bool = False,
    ) -> dict | None:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if session_id:
            clauses.append("id = %(session_id)s")
            params["session_id"] = UUID(session_id)
        if plate:
            clauses.append("detected_plate = %(plate)s")
            params["plate"] = plate
        if university_id:
            clauses.append("university_id = %(university_id)s")
            params["university_id"] = UUID(university_id)
        if require_open:
            clauses.append("session_status = 'open'")
        if require_visitor:
            clauses.append("session_type = 'visitor'")
        if not clauses:
            return None
        cursor.execute(
            f"SELECT * FROM parking_sessions WHERE {' AND '.join(clauses)} ORDER BY entry_time DESC LIMIT 1",
            params,
        )
        return cursor.fetchone()

    def _latest_payment(self, cursor, parking_session_id) -> dict | None:
        cursor.execute(
            "SELECT * FROM payments WHERE parking_session_id = %(id)s ORDER BY created_at DESC LIMIT 1",
            {"id": parking_session_id},
        )
        return cursor.fetchone()

    def _upsert_payment(
        self,
        cursor,
        *,
        session_row: dict | None,
        payment_status: str,
        amount: float,
        payment_method: str | None,
        cashier_user_id: str | None,
        notes: str | None,
        set_paid_at: bool,
    ) -> dict | None:
        if session_row is None:
            return None
        cursor.execute("SELECT nextval('payments_receipt_seq') AS seq")
        seq = cursor.fetchone()["seq"]
        receipt_number = f"REC-{datetime.now(UTC):%Y%m%d}-{seq:04d}"
        try:
            collected_by = UUID(cashier_user_id) if cashier_user_id else None
        except ValueError:
            collected_by = None
        cursor.execute(
            """
            INSERT INTO payments (
                id, university_id, parking_session_id, collected_by_user_id, reference_code,
                amount, currency, payment_method, payment_status, paid_at, notes
            )
            VALUES (
                gen_random_uuid(), %(university_id)s, %(session_id)s, %(collected_by)s, %(reference_code)s,
                %(amount)s, 'USD', %(payment_method)s, %(payment_status)s, %(paid_at)s, %(notes)s
            )
            RETURNING *
            """,
            {
                "university_id": session_row["university_id"],
                "session_id": session_row["id"],
                "collected_by": collected_by,
                "reference_code": receipt_number,
                "amount": round(float(amount), 2),
                "payment_method": payment_method,
                "payment_status": payment_status,
                "paid_at": datetime.now(UTC) if set_paid_at else None,
                "notes": notes.strip() if notes else None,
            },
        )
        return cursor.fetchone()

    def _to_shadow_dict(self, session_row: dict, payment_row: dict | None) -> dict:
        paid_at = payment_row.get("paid_at") if payment_row else None
        payment_valid_until = None
        if paid_at is not None:
            payment_valid_until = paid_at + timedelta(minutes=settings.payment_grace_minutes)
        return {
            "session_id": str(session_row["id"]),
            "university_id": str(session_row["university_id"]) if session_row.get("university_id") else None,
            "plate_text": session_row["detected_plate"],
            "qr_code": f"QR-{session_row['detected_plate']}",
            "entry_time": session_row["entry_time"],
            "exit_time": session_row.get("exit_time"),
            "session_status": _app_session_status(session_row["session_status"]),
            "access_type": _app_access_type(session_row["session_type"]),
            "payment_status": (payment_row["payment_status"].upper() if payment_row else "PENDING"),
            "cashier_user_id": str(payment_row["collected_by_user_id"]) if payment_row and payment_row.get("collected_by_user_id") else None,
            "amount": float(payment_row["amount"]) if payment_row else None,
            "paid_amount": float(payment_row["amount"]) if payment_row and payment_row["payment_status"] == "paid" else None,
            "payment_method": payment_row.get("payment_method") if payment_row else None,
            "paid_at": paid_at,
            "payment_valid_until": payment_valid_until,
            "receipt_number": payment_row.get("reference_code") if payment_row else None,
            "notes": payment_row.get("notes") if payment_row else None,
            "currency": "USD",
        }

    def _connect(self):
        last_error: OperationalError | None = None
        for attempt in range(1, 4):
            try:
                return connect(
                    host=settings.postgres_core_host,
                    port=settings.postgres_core_internal_port,
                    dbname=settings.postgres_core_db,
                    user=settings.postgres_core_user,
                    password=settings.postgres_core_password,
                    connect_timeout=3,
                )
            except OperationalError as exc:
                last_error = exc
                logger.warning(
                    "payment_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
                    attempt,
                    settings.postgres_core_host,
                    settings.postgres_core_internal_port,
                    settings.postgres_core_db,
                    exc,
                )
                if attempt < 3:
                    sleep(0.5)
        assert last_error is not None
        raise last_error
