from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import uuid


class UserRepository:
    UCE_ID = "11111111-1111-1111-1111-111111111111"

    def __init__(self) -> None:
        now = datetime.now(UTC)
        self._universities = getattr(
            self.__class__,
            "_universities",
            {
                self.UCE_ID: {
                    "id": self.UCE_ID,
                    "name": "Universidad Central del Ecuador",
                    "code": "UCE",
                    "city": "Quito",
                    "status": "ACTIVE",
                    "created_at": now,
                }
            },
        )
        self._users = getattr(
            self.__class__,
            "_users",
            self._seed_users(now),
        )
        self.__class__._universities = self._universities
        self.__class__._users = self._users

    def get_user(self, username: str) -> dict | None:
        record = self._users.get(username.strip().lower())
        return deepcopy(record) if record else None

    def verify_password(self, record: dict, password: str) -> bool:
        expected = record.get("password_hash", "")
        return expected == self.hash_password(record["username"], password)

    def list_universities(self, *, actor_role: str, actor_university_id: str | None) -> list[dict]:
        items = [deepcopy(item) for item in self._universities.values()]
        if actor_role != "SUPER_ADMIN" and actor_university_id:
            items = [item for item in items if item["id"] == actor_university_id]
        items.sort(key=lambda item: item["name"])
        return items

    def create_university(self, payload: dict) -> dict:
        now = datetime.now(UTC)
        normalized_code = payload["code"].strip().upper()
        for university in self._universities.values():
            if university["code"] == normalized_code:
                raise ValueError("University code already exists")
        university_id = str(uuid.uuid4())
        record = {
            "id": university_id,
            "name": payload["name"].strip(),
            "code": normalized_code,
            "city": payload["city"].strip(),
            "status": payload.get("status", "ACTIVE").strip().upper(),
            "created_at": now,
        }
        self._universities[university_id] = record
        return deepcopy(record)

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

        items = [deepcopy(item) for item in self._users.values()]
        if target_university_id:
            items = [item for item in items if item.get("university_id") == target_university_id]
        if role:
            normalized_role = role.strip().upper()
            items = [item for item in items if item["role"] == normalized_role]
        items.sort(key=lambda item: (item["role"], item["username"]))
        return items

    def create_user(
        self,
        payload: dict,
        *,
        actor_role: str,
        actor_university_id: str | None,
    ) -> dict:
        username = payload["username"].strip().lower()
        if username in self._users:
            raise ValueError("Username already exists")

        university_id = payload.get("university_id")
        if actor_role != "SUPER_ADMIN":
            university_id = actor_university_id

        if university_id and university_id not in self._universities:
            raise ValueError("University not found")

        now = datetime.now(UTC)
        role = payload["role"].strip().upper()
        record = {
            "id": str(uuid.uuid4()),
            "username": username,
            "password_hash": self.hash_password(username, payload["password"]),
            "full_name": payload["full_name"].strip(),
            "email": payload.get("email"),
            "role": role,
            "roles": [role],
            "university_id": university_id,
            "status": payload.get("status", "ACTIVE").strip().upper(),
            "created_at": now,
        }
        self._users[username] = record
        return deepcopy(record)

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

    def _seed_users(self, now: datetime) -> dict[str, dict]:
        return {
            record["username"]: record
            for record in [
                self._user_record(
                    id="user-super-admin-001",
                    username="super.admin",
                    full_name="Super Administrador",
                    email="super.admin@smartparking.local",
                    role="SUPER_ADMIN",
                    university_id=None,
                    created_at=now,
                ),
                self._user_record(
                    id="user-university-admin-001",
                    username="admin.university",
                    full_name="Administrador Universidad",
                    email="admin.university@uce.edu.ec",
                    role="UNIVERSITY_ADMIN",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-cashier-001",
                    username="cashier.uce",
                    full_name="Caja UCE",
                    email="cashier@uce.edu.ec",
                    role="CASHIER",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-member-manager-001",
                    username="members.uce",
                    full_name="Gestor de Miembros UCE",
                    email="members@uce.edu.ec",
                    role="MEMBER_MANAGER",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-security-001",
                    username="security.uce",
                    full_name="Seguridad UCE",
                    email="security@uce.edu.ec",
                    role="SECURITY",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-auditor-001",
                    username="auditor.uce",
                    full_name="Auditor UCE",
                    email="auditor@uce.edu.ec",
                    role="AUDITOR",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-gate-operator-001",
                    username="gate.operator",
                    full_name="Operador de Garita",
                    email="gate.operator@uce.edu.ec",
                    role="SECURITY",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-cashier-legacy-001",
                    username="cashier.user",
                    full_name="Caja Demo",
                    email="cashier.demo@uce.edu.ec",
                    role="CASHIER",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
                self._user_record(
                    id="user-security-legacy-001",
                    username="security.agent",
                    full_name="Seguridad Demo",
                    email="security.demo@uce.edu.ec",
                    role="SECURITY",
                    university_id=self.UCE_ID,
                    created_at=now,
                ),
            ]
        }

    def _user_record(
        self,
        *,
        id: str,
        username: str,
        full_name: str,
        email: str,
        role: str,
        university_id: str | None,
        created_at: datetime,
    ) -> dict:
        return {
            "id": id,
            "username": username.strip().lower(),
            "password_hash": self.hash_password(username, "demo1234!"),
            "full_name": full_name,
            "email": email,
            "role": role,
            "roles": [role],
            "university_id": university_id,
            "status": "ACTIVE",
            "created_at": created_at,
        }
