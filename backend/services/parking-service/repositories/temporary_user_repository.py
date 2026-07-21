import json
import logging
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Any
from uuid import UUID, uuid4

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)


def _safe_uuid(value: str | None) -> UUID | None:
    # gate_id (y a veces otras referencias) llegan como strings de demo
    # (ej. "gate-norte") en vez de UUIDs reales, porque la tabla `gates` aun
    # no tiene repositorio que la valide. Esto es un campo de contexto
    # forense, no una FK critica: si no es un UUID valido, se guarda como
    # NULL en vez de tumbar todo el registro best-effort.
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


class TemporaryUserRepository:
    """Persistencia de usuarios temporales de visitantes en la BD core.

    Conserva los datos del visitante (placa, referencia a su foto y template
    facial, sesion de entrada) durante una ventana de retencion configurable
    (``TEMP_USER_RETENTION_DAYS``, por defecto 30 dias), para consulta forense
    ante inconsistencias en la salida.
    """

    def create(
        self,
        *,
        university_id: str,
        plate: str,
        full_name: str | None,
        face_template_id: str | None,
        entry_face_evidence_id: str | None,
        entry_plate_evidence_id: str | None,
        entry_session_id: str | None,
        entry_gate_id: str | None,
        face_model_name: str | None,
        liveness_score: float | None,
        metadata: dict | None = None,
        retention_days: int | None = None,
        temp_user_id: str | None = None,
    ) -> dict:
        temp_user_id = temp_user_id or str(uuid4())
        days = retention_days if retention_days is not None else settings.temp_user_retention_days
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO temporary_users (
                        id,
                        university_id,
                        plate,
                        full_name,
                        person_type,
                        face_template_id,
                        entry_face_evidence_id,
                        entry_plate_evidence_id,
                        entry_session_id,
                        entry_gate_id,
                        face_model_name,
                        liveness_score,
                        metadata,
                        status,
                        expires_at
                    )
                    VALUES (
                        %(id)s,
                        %(university_id)s,
                        %(plate)s,
                        %(full_name)s,
                        'visitor',
                        %(face_template_id)s,
                        %(entry_face_evidence_id)s,
                        %(entry_plate_evidence_id)s,
                        %(entry_session_id)s,
                        %(entry_gate_id)s,
                        %(face_model_name)s,
                        %(liveness_score)s,
                        %(metadata)s,
                        'active',
                        %(expires_at)s
                    )
                    RETURNING
                        id,
                        university_id,
                        plate,
                        full_name,
                        face_template_id,
                        entry_face_evidence_id,
                        entry_plate_evidence_id,
                        entry_session_id,
                        entry_gate_id,
                        face_model_name,
                        liveness_score,
                        metadata,
                        status,
                        created_at,
                        expires_at
                    """,
                    {
                        "id": temp_user_id,
                        "university_id": UUID(university_id),
                        "plate": plate,
                        "full_name": full_name,
                        "face_template_id": _safe_uuid(face_template_id),
                        "entry_face_evidence_id": _safe_uuid(entry_face_evidence_id),
                        "entry_plate_evidence_id": _safe_uuid(entry_plate_evidence_id),
                        "entry_session_id": _safe_uuid(entry_session_id),
                        "entry_gate_id": _safe_uuid(entry_gate_id),
                        "face_model_name": face_model_name,
                        "liveness_score": liveness_score,
                        "metadata": json.dumps(metadata or {}),
                        "expires_at": expires_at,
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._normalize_row(row)

    def get_active_by_plate(self, university_id: str, plate: str) -> dict | None:
        """Usuario temporal vigente (activo y no caducado) mas reciente para una placa."""
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        university_id,
                        plate,
                        full_name,
                        face_template_id,
                        entry_face_evidence_id,
                        entry_plate_evidence_id,
                        entry_session_id,
                        entry_gate_id,
                        face_model_name,
                        liveness_score,
                        metadata,
                        status,
                        created_at,
                        expires_at
                    FROM temporary_users
                    WHERE university_id = %(university_id)s
                      AND plate = %(plate)s
                      AND status = 'active'
                      AND expires_at > NOW()
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    {"university_id": UUID(university_id), "plate": plate},
                )
                row = cursor.fetchone()
        return None if row is None else self._normalize_row(row)

    def list_by_plate(self, plate: str, include_expired: bool = True) -> list[dict]:
        """Historial de usuarios temporales por placa (para consulta del guardia)."""
        clause = "" if include_expired else "AND status = 'active' AND expires_at > NOW()"
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        id,
                        university_id,
                        plate,
                        full_name,
                        face_template_id,
                        entry_face_evidence_id,
                        entry_plate_evidence_id,
                        entry_session_id,
                        entry_gate_id,
                        face_model_name,
                        liveness_score,
                        metadata,
                        status,
                        created_at,
                        expires_at
                    FROM temporary_users
                    WHERE plate = %(plate)s
                    {clause}
                    ORDER BY created_at DESC
                    """,
                    {"plate": plate},
                )
                rows = cursor.fetchall()
        return [self._normalize_row(row) for row in rows]

    def mark_status(self, temp_user_id: str, status: str) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE temporary_users SET status = %(status)s WHERE id = %(id)s",
                    {"status": status, "id": UUID(temp_user_id)},
                )
            connection.commit()

    def expire_stale(self) -> int:
        """Marca como 'expired' los registros vencidos. Devuelve cuantos cambio."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE temporary_users SET status = 'expired' "
                    "WHERE status = 'active' AND expires_at <= NOW()"
                )
                changed = cursor.rowcount
            connection.commit()
        return changed

    # ------------------------------------------------------------------ #
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
                    "temporary_user_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
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

    def _normalize_row(self, row: dict[str, Any]) -> dict:
        normalized = dict(row)
        for key in (
            "id",
            "university_id",
            "face_template_id",
            "entry_face_evidence_id",
            "entry_plate_evidence_id",
            "entry_session_id",
            "entry_gate_id",
        ):
            if normalized.get(key) is not None:
                normalized[key] = str(normalized[key])
        if normalized.get("liveness_score") is not None:
            normalized["liveness_score"] = float(normalized["liveness_score"])
        for key in ("created_at", "expires_at"):
            value = normalized.get(key)
            if isinstance(value, datetime):
                normalized[key] = value.isoformat().replace("+00:00", "Z")
        return normalized
