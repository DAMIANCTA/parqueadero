import logging
from time import sleep
from uuid import UUID

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)


class AccessEventRepository:
    def create_entry_event(
        self,
        university_id: str,
        gate_id: str,
        plate_text: str,
        session_id: str | None,
        result: str,
        reason: str,
    ) -> dict:
        event_type = "entry_granted" if result == "success" else "entry_denied"
        return self._create_event(university_id, gate_id, plate_text, session_id, event_type, result, reason)

    def create_exit_event(
        self,
        university_id: str,
        gate_id: str,
        plate_text: str,
        session_id: str | None,
        result: str,
        reason: str,
    ) -> dict:
        event_type = "exit_granted" if result == "success" else "exit_denied"
        return self._create_event(university_id, gate_id, plate_text, session_id, event_type, result, reason)

    def _create_event(
        self,
        university_id: str,
        gate_id: str,
        plate_text: str,
        session_id: str | None,
        event_type: str,
        result: str,
        reason: str,
    ) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO access_events (
                        id, university_id, parking_session_id, gate_id, event_type, result, reason
                    )
                    VALUES (
                        gen_random_uuid(), %(university_id)s, %(session_id)s, %(gate_id)s,
                        %(event_type)s, %(result)s, %(reason)s
                    )
                    RETURNING id
                    """,
                    {
                        "university_id": UUID(university_id),
                        "session_id": UUID(session_id) if session_id else None,
                        "gate_id": self._resolve_gate_id(cursor, gate_id),
                        "event_type": event_type,
                        "result": result,
                        "reason": reason,
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return {
            "id": str(row["id"]),
            "university_id": university_id,
            "gate_id": gate_id,
            "plate_text": plate_text,
            "session_id": session_id,
            "result": result,
            "reason": reason,
        }

    def _resolve_gate_id(self, cursor, gate_ref: str) -> UUID | None:
        try:
            return UUID(gate_ref)
        except (ValueError, AttributeError):
            pass
        code = "".join(ch for ch in gate_ref.strip().upper() if ch.isalnum())
        cursor.execute("SELECT id FROM gates WHERE code = %(code)s LIMIT 1", {"code": code})
        row = cursor.fetchone()
        return row["id"] if row else None

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
                    "access_event_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
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
