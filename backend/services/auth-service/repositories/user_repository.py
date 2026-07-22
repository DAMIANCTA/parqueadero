from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from time import sleep
from typing import Any
from uuid import UUID

from psycopg import IntegrityError, OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)

# Traduce entre el string de rol de aplicacion (usado por ROLE_PERMISSIONS
# en services/auth_service.py) y el role_key real de la tabla `roles`
# (ver database/postgres-core/seeds/001_seed_reference_data.sql y la
# migracion 005 que agrego 'driver').
ROLE_TO_KEY = {
    "SUPER_ADMIN": "superadmin",
    "UNIVERSITY_ADMIN": "admin_university",
    "CASHIER": "cashier",
    "MEMBER_MANAGER": "member_manager",
    "SECURITY": "security",
    "AUDITOR": "auditor",
    "DRIVER": "driver",
}
KEY_TO_ROLE = {value: key for key, value in ROLE_TO_KEY.items()}

_SEED_PASSWORD = "demo1234!"
_SEED_USERS = [
    ("super.admin", "Super Administrador", "super.admin@smartparking.local", "SUPER_ADMIN", None),
    ("admin.university", "Administrador Universidad", "admin.university@uce.edu.ec", "UNIVERSITY_ADMIN", "UCE_ID"),
    ("cashier.uce", "Caja UCE", "cashier@uce.edu.ec", "CASHIER", "UCE_ID"),
    ("members.uce", "Gestor de Miembros UCE", "members@uce.edu.ec", "MEMBER_MANAGER", "UCE_ID"),
    ("security.uce", "Seguridad UCE", "security@uce.edu.ec", "SECURITY", "UCE_ID"),
    ("auditor.uce", "Auditor UCE", "auditor@uce.edu.ec", "AUDITOR", "UCE_ID"),
    ("gate.operator", "Operador de Garita", "gate.operator@uce.edu.ec", "SECURITY", "UCE_ID"),
    ("cashier.user", "Caja Demo", "cashier.demo@uce.edu.ec", "CASHIER", "UCE_ID"),
    ("security.agent", "Seguridad Demo", "security.demo@uce.edu.ec", "SECURITY", "UCE_ID"),
]


class UserRepository:
    UCE_ID = "11111111-1111-1111-1111-111111111111"

    def __init__(self) -> None:
        self._ensure_seed_users()

    def get_user(self, username: str) -> dict | None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT u.id, u.university_id, u.username, u.email, u.password_hash,
                           u.first_name, u.last_name, u.document_number, u.phone,
                           u.status, u.created_at, r.role_key
                    FROM users u
                    JOIN roles r ON r.id = u.role_id
                    WHERE u.username = %(username)s
                    """,
                    {"username": username.strip().lower()},
                )
                row = cursor.fetchone()
        return None if row is None else self._to_user_dict(row)

    def verify_password(self, record: dict, password: str) -> bool:
        expected = record.get("password_hash", "")
        return expected == self.hash_password(record["username"], password)

    def set_password(self, username: str, new_password: str) -> None:
        normalized = username.strip().lower()
        password_hash = self.hash_password(normalized, new_password)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password_hash = %(password_hash)s WHERE username = %(username)s",
                    {"password_hash": password_hash, "username": normalized},
                )
            connection.commit()

    def list_universities(self, *, actor_role: str, actor_university_id: str | None) -> list[dict]:
        clause = ""
        params: dict[str, Any] = {}
        if actor_role != "SUPER_ADMIN" and actor_university_id:
            clause = "WHERE id = %(university_id)s"
            params["university_id"] = UUID(actor_university_id)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT id, name, code, city, status, created_at
                    FROM universities
                    {clause}
                    ORDER BY name
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._normalize_row(row) for row in rows]

    def create_university(self, payload: dict) -> dict:
        normalized_code = payload["code"].strip().upper()
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                try:
                    cursor.execute(
                        """
                        INSERT INTO universities (id, name, code, city, status)
                        VALUES (gen_random_uuid(), %(name)s, %(code)s, %(city)s, %(status)s)
                        RETURNING id, name, code, city, status, created_at
                        """,
                        {
                            "name": payload["name"].strip(),
                            "code": normalized_code,
                            "city": payload["city"].strip(),
                            "status": payload.get("status", "ACTIVE").strip().lower(),
                        },
                    )
                    row = cursor.fetchone()
                except IntegrityError as exc:
                    connection.rollback()
                    raise ValueError("University code already exists") from exc
                connection.commit()
        return self._normalize_row(row)

    def list_users(
        self,
        *,
        actor_role: str,
        actor_university_id: str | None,
        university_id: str | None = None,
        role: str | None = None,
    ) -> list[dict]:
        target_university_id = university_id
        if actor_role != "SUPER_ADMIN":
            target_university_id = actor_university_id

        clauses: list[str] = []
        params: dict[str, Any] = {}
        if target_university_id:
            clauses.append("u.university_id = %(university_id)s")
            params["university_id"] = UUID(target_university_id)
        if role:
            clauses.append("r.role_key = %(role_key)s")
            params["role_key"] = ROLE_TO_KEY.get(role.strip().upper(), role.strip().lower())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT u.id, u.university_id, u.username, u.email, u.password_hash,
                           u.first_name, u.last_name, u.document_number, u.phone,
                           u.status, u.created_at, r.role_key
                    FROM users u
                    JOIN roles r ON r.id = u.role_id
                    {where}
                    ORDER BY r.role_key, u.username
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._to_user_dict(row) for row in rows]

    def create_user(
        self,
        payload: dict,
        *,
        actor_role: str,
        actor_university_id: str | None,
    ) -> dict:
        username = payload["username"].strip().lower()
        university_id = payload.get("university_id")
        if actor_role != "SUPER_ADMIN":
            university_id = actor_university_id

        role = payload["role"].strip().upper()
        role_key = ROLE_TO_KEY.get(role, role.lower())
        first_name, last_name = self._split_full_name(payload["full_name"])
        now_status = payload.get("status", "ACTIVE").strip().lower()

        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                if university_id:
                    cursor.execute(
                        "SELECT 1 FROM universities WHERE id = %(id)s",
                        {"id": UUID(university_id)},
                    )
                    if cursor.fetchone() is None:
                        raise ValueError("University not found")

                cursor.execute("SELECT id FROM roles WHERE role_key = %(role_key)s", {"role_key": role_key})
                role_row = cursor.fetchone()
                if role_row is None:
                    raise ValueError(f"Role '{role}' not found")

                try:
                    cursor.execute(
                        """
                        INSERT INTO users (
                            id, university_id, role_id, username, email, password_hash,
                            first_name, last_name, document_number, phone, status
                        )
                        VALUES (
                            gen_random_uuid(), %(university_id)s, %(role_id)s, %(username)s,
                            %(email)s, %(password_hash)s, %(first_name)s, %(last_name)s,
                            %(document_number)s, %(phone)s, %(status)s
                        )
                        RETURNING id, university_id, username, email, password_hash,
                                  first_name, last_name, document_number, phone, status, created_at
                        """,
                        {
                            "university_id": UUID(university_id) if university_id else None,
                            "role_id": role_row["id"],
                            "username": username,
                            "email": payload.get("email"),
                            "password_hash": self.hash_password(username, payload["password"]),
                            "first_name": first_name,
                            "last_name": last_name,
                            "document_number": payload.get("document_number"),
                            "phone": payload.get("phone"),
                            "status": now_status,
                        },
                    )
                    row = cursor.fetchone()
                except IntegrityError as exc:
                    connection.rollback()
                    constraint = getattr(exc, "diag", None) and exc.diag.constraint_name
                    if constraint == "uq_users_email":
                        raise ValueError("Email already exists") from exc
                    if constraint == "uq_users_username":
                        raise ValueError("Username already exists") from exc
                    raise
                connection.commit()
        return self._to_user_dict({**row, "role_key": role_key})

    @staticmethod
    def hash_password(username: str, password: str) -> str:
        normalized_username = username.strip().lower().encode("utf-8")
        normalized_password = password.encode("utf-8")
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            normalized_password,
            b"smart-parking-auth::" + normalized_username,
            120_000,
        )
        return digest.hex()

    # ------------------------------------------------------------------ #
    def _ensure_seed_users(self) -> None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT role_key, id FROM roles")
                role_ids = {row["role_key"]: row["id"] for row in cursor.fetchall()}

                for username, full_name, email, role, university_ref in _SEED_USERS:
                    role_key = ROLE_TO_KEY[role]
                    role_id = role_ids.get(role_key)
                    if role_id is None:
                        continue
                    university_id = UUID(self.UCE_ID) if university_ref == "UCE_ID" else None
                    first_name, last_name = self._split_full_name(full_name)
                    cursor.execute(
                        """
                        INSERT INTO users (
                            id, university_id, role_id, username, email, password_hash,
                            first_name, last_name, status
                        )
                        VALUES (
                            gen_random_uuid(), %(university_id)s, %(role_id)s, %(username)s,
                            %(email)s, %(password_hash)s, %(first_name)s, %(last_name)s, 'active'
                        )
                        ON CONFLICT (username) DO NOTHING
                        """,
                        {
                            "university_id": university_id,
                            "role_id": role_id,
                            "username": username,
                            "email": email,
                            "password_hash": self.hash_password(username, _SEED_PASSWORD),
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )
            connection.commit()

    @staticmethod
    def _split_full_name(full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(" ", 1)
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]

    def _to_user_dict(self, row: dict[str, Any]) -> dict:
        first_name = row.get("first_name") or ""
        last_name = row.get("last_name") or ""
        full_name = f"{first_name} {last_name}".strip() or row["username"]
        role_key = row["role_key"]
        role = KEY_TO_ROLE.get(role_key, role_key.upper())
        return {
            "id": str(row["id"]),
            "username": row["username"],
            "password_hash": row.get("password_hash", ""),
            "full_name": full_name,
            "email": row.get("email"),
            "document_number": row.get("document_number"),
            "phone": row.get("phone"),
            "role": role,
            "roles": [role],
            "university_id": str(row["university_id"]) if row.get("university_id") else None,
            "status": (row.get("status") or "active").upper(),
            "created_at": row["created_at"] if isinstance(row.get("created_at"), datetime) else datetime.now(UTC),
        }

    def _normalize_row(self, row: dict[str, Any]) -> dict:
        normalized = dict(row)
        if normalized.get("id") is not None:
            normalized["id"] = str(normalized["id"])
        normalized["status"] = (normalized.get("status") or "active").upper()
        return normalized

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
                    "user_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
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
