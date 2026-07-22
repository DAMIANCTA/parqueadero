import logging
from datetime import UTC, datetime
from time import sleep
from typing import Any
from uuid import UUID, uuid4

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)

DEMO_UNIVERSITY_ID = "11111111-1111-1111-1111-111111111111"
DEMO_CAMPUS_ID = "22222222-2222-2222-2222-222222222222"
DEMO_GATE_CODE = "GARITA01"
# (session_id fijo, plate, payment_status, entry_offset_minutes) - mismas
# sesiones "ya adentro" que el mock traia precargadas para poder probar el
# flujo de salida sin tener que hacer una entrada real primero.
_SEED_ACTIVE_SESSIONS = [
    ("66666666-6666-6666-6666-666666666601", "VIS1234", "paid", "face-visitor-001", 45),
    ("66666666-6666-6666-6666-666666666602", "VISPEND", "pending", "face-visitor-002", 20),
]


def _db_session_status(app_status: str) -> str:
    return "open" if app_status == "INSIDE" else "closed"


def _app_session_status(db_status: str) -> str:
    return "INSIDE" if db_status == "open" else "OUTSIDE"


def _db_session_type(access_type: str) -> str:
    return "internal" if access_type == "MEMBER" else "visitor"


def _app_access_type(session_type: str) -> str:
    return "MEMBER" if session_type == "internal" else "VISITOR"


def _slug_code(value: str) -> str:
    return "".join(ch for ch in value.strip().upper() if ch.isalnum()) or "DEFAULT"


class ParkingSessionRepository:
    def __init__(self) -> None:
        self._ensure_seed_sessions()

    def has_active_session_by_plate(self, plate_text: str) -> bool:
        return self.get_active_session_by_plate(plate_text) is not None

    def get_active_session_by_plate(self, plate_text: str) -> dict | None:
        normalized_plate = self._normalize_plate(plate_text)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM parking_sessions
                    WHERE detected_plate = %(plate)s AND session_status = 'open'
                    ORDER BY entry_time DESC
                    LIMIT 1
                    """,
                    {"plate": normalized_plate},
                )
                row = cursor.fetchone()
        return None if row is None else self._session_summary(row)

    def get_active_visitor_session_by_plate(self, plate_text: str) -> dict | None:
        session = self.get_active_session_by_plate(plate_text)
        if session is None or session.get("access_type") != "VISITOR":
            return None
        return session

    def create_new_session_for_entry(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate_text: str,
        person_type: str,
        entry_face_image_id: str,
        access_type: str = "VISITOR",
        payment_status: str | None = None,
        person_id: str | None = None,
        person_name: str | None = None,
        role_type: str | None = None,
        vehicle_id: str | None = None,
        entry_face_evidence_id: str | None = None,
        entry_plate_evidence_id: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        del entry_face_image_id  # no columna dedicada; la evidencia real va por entry_face_evidence_id
        normalized_plate = self._normalize_plate(plate_text)
        resolved_payment_status = (payment_status or ("PENDING" if access_type == "VISITOR" else "NOT_REQUIRED")).lower()

        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                university_uuid = UUID(university_id)
                campus_uuid = self._resolve_campus_id(cursor, university_uuid, campus_id)
                gate_uuid = self._resolve_gate_id(cursor, university_uuid, campus_uuid, gate_id)
                cursor.execute(
                    """
                    INSERT INTO parking_sessions (
                        id, university_id, campus_id, vehicle_id, person_id, entry_gate_id,
                        session_type, session_status, detected_plate, payment_required, payment_status,
                        entry_time, person_name, person_type, role_type,
                        entry_face_evidence_id, entry_plate_evidence_id
                    )
                    VALUES (
                        %(id)s, %(university_id)s, %(campus_id)s, %(vehicle_id)s, %(person_id)s, %(gate_id)s,
                        %(session_type)s, 'open', %(plate)s, %(payment_required)s, %(payment_status)s,
                        NOW(), %(person_name)s, %(person_type)s, %(role_type)s,
                        %(entry_face_evidence_id)s, %(entry_plate_evidence_id)s
                    )
                    RETURNING *
                    """,
                    {
                        "id": UUID(session_id) if session_id else uuid4(),
                        "university_id": university_uuid,
                        "campus_id": campus_uuid,
                        "vehicle_id": UUID(vehicle_id) if vehicle_id else None,
                        "person_id": UUID(person_id) if person_id else None,
                        "gate_id": gate_uuid,
                        "session_type": _db_session_type(access_type),
                        "plate": normalized_plate,
                        "payment_required": access_type == "VISITOR",
                        "payment_status": resolved_payment_status,
                        "person_name": person_name,
                        "person_type": person_type,
                        "role_type": role_type,
                        "entry_face_evidence_id": UUID(entry_face_evidence_id) if entry_face_evidence_id else None,
                        "entry_plate_evidence_id": UUID(entry_plate_evidence_id) if entry_plate_evidence_id else None,
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._session_summary(row)

    def find_active_session_by_plate(self, university_id: str, plate_text: str) -> dict | None:
        del university_id
        return self.get_active_session_by_plate(plate_text)

    def close_session(
        self,
        session_id: str,
        plate_text: str,
        person_type: str,
        payment_status: str,
        access_type: str | None = None,
        exit_face_evidence_id: str | None = None,
        exit_plate_evidence_id: str | None = None,
    ) -> dict:
        del plate_text  # la placa ya quedo fijada en la entrada, no se re-normaliza en la salida
        assignments = [
            "session_status = 'closed'",
            "payment_status = %(payment_status)s",
            "person_type = %(person_type)s",
            "exit_face_evidence_id = %(exit_face_evidence_id)s",
            "exit_plate_evidence_id = %(exit_plate_evidence_id)s",
            "exit_time = NOW()",
        ]
        params: dict[str, Any] = {
            "id": UUID(session_id),
            "payment_status": payment_status.lower(),
            "person_type": person_type,
            "exit_face_evidence_id": UUID(exit_face_evidence_id) if exit_face_evidence_id else None,
            "exit_plate_evidence_id": UUID(exit_plate_evidence_id) if exit_plate_evidence_id else None,
        }
        if access_type is not None:
            assignments.append("session_type = %(session_type)s")
            params["session_type"] = _db_session_type(access_type)

        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"UPDATE parking_sessions SET {', '.join(assignments)} WHERE id = %(id)s RETURNING *",
                    params,
                )
                row = cursor.fetchone()
            connection.commit()
        return self._session_summary(row)

    def attach_evidence(
        self,
        session_id: str,
        *,
        operation: str,
        face_evidence_id: str | None = None,
        plate_evidence_id: str | None = None,
    ) -> None:
        if operation not in ("entry", "exit"):
            return
        assignments = []
        params: dict[str, Any] = {"id": UUID(session_id)}
        if face_evidence_id:
            assignments.append(f"{operation}_face_evidence_id = %(face_evidence_id)s")
            params["face_evidence_id"] = UUID(face_evidence_id)
        if plate_evidence_id:
            assignments.append(f"{operation}_plate_evidence_id = %(plate_evidence_id)s")
            params["plate_evidence_id"] = UUID(plate_evidence_id)
        if not assignments:
            return
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE parking_sessions SET {', '.join(assignments)} WHERE id = %(id)s",
                    params,
                )
            connection.commit()

    def list_history(
        self,
        university_id: str | None = None,
        limit: int = 100,
        plate_text: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit}
        if university_id:
            clauses.append("university_id = %(university_id)s")
            params["university_id"] = UUID(university_id)
        if plate_text:
            clauses.append("detected_plate = %(plate)s")
            params["plate"] = self._normalize_plate(plate_text)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT * FROM parking_sessions
                    {where}
                    ORDER BY COALESCE(exit_time, entry_time) DESC
                    LIMIT %(limit)s
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._history_entry(row) for row in rows]

    # ------------------------------------------------------------------ #
    def _normalize_plate(self, plate_text: str) -> str:
        return plate_text.strip().upper().replace(" ", "").replace("-", "")

    def _resolve_campus_id(self, cursor, university_id: UUID, campus_ref: str) -> UUID:
        try:
            return UUID(campus_ref)
        except (ValueError, AttributeError):
            pass
        code = _slug_code(campus_ref)
        cursor.execute(
            "SELECT id FROM campuses WHERE university_id = %(university_id)s AND code = %(code)s",
            {"university_id": university_id, "code": code},
        )
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute(
            """
            INSERT INTO campuses (id, university_id, name, code, status)
            VALUES (gen_random_uuid(), %(university_id)s, %(name)s, %(code)s, 'active')
            ON CONFLICT (university_id, code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            {"university_id": university_id, "name": campus_ref, "code": code},
        )
        return cursor.fetchone()["id"]

    def _resolve_gate_id(self, cursor, university_id: UUID, campus_id: UUID, gate_ref: str) -> UUID:
        try:
            return UUID(gate_ref)
        except (ValueError, AttributeError):
            pass
        code = _slug_code(gate_ref)
        cursor.execute(
            "SELECT id FROM gates WHERE campus_id = %(campus_id)s AND code = %(code)s",
            {"campus_id": campus_id, "code": code},
        )
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute(
            """
            INSERT INTO gates (id, university_id, campus_id, name, code, direction_type, status)
            VALUES (gen_random_uuid(), %(university_id)s, %(campus_id)s, %(name)s, %(code)s, 'bidirectional', 'active')
            ON CONFLICT (campus_id, code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            {"university_id": university_id, "campus_id": campus_id, "name": gate_ref, "code": code},
        )
        return cursor.fetchone()["id"]

    def _ensure_seed_sessions(self) -> None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                university_uuid = UUID(DEMO_UNIVERSITY_ID)
                campus_uuid = self._resolve_campus_id(cursor, university_uuid, DEMO_CAMPUS_ID)
                gate_uuid = self._resolve_gate_id(cursor, university_uuid, campus_uuid, DEMO_GATE_CODE)
                for session_id, plate, payment_status, face_evidence_id, offset_minutes in _SEED_ACTIVE_SESSIONS:
                    cursor.execute(
                        """
                        INSERT INTO parking_sessions (
                            id, university_id, campus_id, entry_gate_id, session_type, session_status,
                            detected_plate, payment_required, payment_status, entry_time, person_type
                        )
                        VALUES (
                            %(id)s, %(university_id)s, %(campus_id)s, %(gate_id)s, 'visitor', 'open',
                            %(plate)s, true, %(payment_status)s, NOW() - (%(offset)s || ' minutes')::interval, 'visitor'
                        )
                        ON CONFLICT (id) DO NOTHING
                        """,
                        {
                            "id": UUID(session_id),
                            "university_id": university_uuid,
                            "campus_id": campus_uuid,
                            "gate_id": gate_uuid,
                            "plate": plate,
                            "payment_status": payment_status,
                            "offset": offset_minutes,
                        },
                    )
            connection.commit()

    def _history_entry(self, row: dict[str, Any]) -> dict:
        return {
            "session_id": str(row["id"]),
            "session_status": _app_session_status(row["session_status"]),
            "access_type": _app_access_type(row["session_type"]),
            "plate_text": row["detected_plate"],
            "person_name": row.get("person_name"),
            "payment_status": row["payment_status"].upper(),
            "entry_time": row["entry_time"].isoformat().replace("+00:00", "Z") if row.get("entry_time") else None,
            "exit_time": row["exit_time"].isoformat().replace("+00:00", "Z") if row.get("exit_time") else None,
            "entry_face_evidence_id": str(row["entry_face_evidence_id"]) if row.get("entry_face_evidence_id") else None,
            "entry_plate_evidence_id": str(row["entry_plate_evidence_id"]) if row.get("entry_plate_evidence_id") else None,
            "exit_face_evidence_id": str(row["exit_face_evidence_id"]) if row.get("exit_face_evidence_id") else None,
            "exit_plate_evidence_id": str(row["exit_plate_evidence_id"]) if row.get("exit_plate_evidence_id") else None,
        }

    def _session_summary(self, row: dict[str, Any]) -> dict:
        return {
            "session_id": str(row["id"]),
            "session_status": _app_session_status(row["session_status"]),
            "payment_status": row["payment_status"].upper(),
            "person_type": row.get("person_type"),
            "access_type": _app_access_type(row["session_type"]),
            "plate_text": row["detected_plate"],
            "person_id": str(row["person_id"]) if row.get("person_id") else None,
            "person_name": row.get("person_name"),
            "role_type": row.get("role_type"),
            "vehicle_id": str(row["vehicle_id"]) if row.get("vehicle_id") else None,
            "entry_time": row["entry_time"].isoformat().replace("+00:00", "Z") if row.get("entry_time") else None,
            "exit_time": row["exit_time"].isoformat().replace("+00:00", "Z") if row.get("exit_time") else None,
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
                    "parking_session_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
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
