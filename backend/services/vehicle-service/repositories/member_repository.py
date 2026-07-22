import logging
from datetime import UTC, date, datetime
from time import sleep
from typing import Any
from uuid import UUID

from psycopg import IntegrityError, OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)

# RoleType (API, mayusculas, ver schemas/members.py) <-> persons.person_type
# (columna real, minusculas). STAFF se guarda como 'employee' porque el
# check constraint de `persons` ya usa esa palabra para ese tipo de persona.
ROLE_TYPE_TO_PERSON_TYPE = {
    "STUDENT": "student",
    "TEACHER": "teacher",
    "STAFF": "employee",
    "DRIVER": "driver",
}
PERSON_TYPE_TO_ROLE_TYPE = {value: key for key, value in ROLE_TYPE_TO_PERSON_TYPE.items()}

_SEED_MEMBERS = [
    {
        "document_id": "0102030405",
        "institutional_id": "UCE2026001",
        "full_name": "Ana Belen Torres",
        "email": "ana.torres@uce.edu.ec",
        "role_type": "STUDENT",
    },
    {
        "document_id": "1112131415",
        "institutional_id": "UCE-DOC-100",
        "full_name": "Carlos Mena",
        "email": "carlos.mena@uce.edu.ec",
        "role_type": "TEACHER",
    },
    {
        "document_id": "1617181920",
        "institutional_id": "UCE-ADM-050",
        "full_name": "Maria Fernanda Ruiz",
        "email": "maria.ruiz@uce.edu.ec",
        "role_type": "STAFF",
    },
]
_SEED_VEHICLES = [
    {"plate_text": "ABC1234", "brand": "Chevrolet", "model": "Spark", "color": "Rojo"},
    {"plate_text": "XYZ9876", "brand": "Kia", "model": "Rio", "color": "Blanco"},
    {"plate_text": "EMP2026", "brand": "Hyundai", "model": "Accent", "color": "Gris"},
    {"plate_text": "EXP2026", "brand": "Nissan", "model": "Versa", "color": "Azul"},
]
# (document_id del dueno, plate_text, is_owner)
_SEED_AUTHORIZATIONS = [
    ("0102030405", "ABC1234", True),
    ("1112131415", "XYZ9876", True),
    ("1617181920", "EMP2026", True),
    ("1617181920", "EXP2026", False),
]
# (document_id, plate_text, dias_inicio_relativo, dias_fin_relativo, amount, payment_method, status, receipt_number)
_SEED_PERMITS = [
    ("0102030405", "ABC1234", -7, 23, 15.0, "transfer", "VALID", "MEM-202607-001"),
    ("1112131415", "XYZ9876", -4, 26, 20.0, "cash", "VALID", "MEM-202607-002"),
    ("1617181920", "EXP2026", -40, -10, 20.0, "cash", "EXPIRED", "MEM-202606-010"),
]
_SEED_FACE_PROFILES = [
    ("0102030405", "mock-face-service"),
    ("1112131415", "mock-face-service"),
    ("1617181920", "mock-face-service"),
]


class MemberRepository:
    UNIVERSITY_ID = "11111111-1111-1111-1111-111111111111"

    def __init__(self) -> None:
        self._ensure_seed_data()

    # ------------------------------------------------------------------ #
    # Personas (persons)
    # ------------------------------------------------------------------ #
    def create_member(self, payload: dict) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO persons (
                        id, university_id, user_id, institutional_code, full_name,
                        document_number, email, person_type, status
                    )
                    VALUES (
                        gen_random_uuid(), %(university_id)s, %(user_id)s, %(institutional_id)s,
                        %(full_name)s, %(document_id)s, %(email)s, %(person_type)s, %(status)s
                    )
                    RETURNING id, university_id, user_id, institutional_code, full_name,
                              document_number, email, person_type, status, created_at, updated_at
                    """,
                    {
                        "university_id": UUID(payload["university_id"]),
                        "user_id": payload.get("user_id"),
                        "institutional_id": payload["institutional_id"],
                        "full_name": payload["full_name"],
                        "document_id": payload["document_id"],
                        "email": payload["email"],
                        "person_type": ROLE_TYPE_TO_PERSON_TYPE[payload["role_type"]],
                        "status": payload.get("status", "ACTIVE").lower(),
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._to_member_dict(row)

    def list_members(self, university_id: str | None = None, user_id: str | None = None) -> list[dict]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if university_id:
            clauses.append("university_id = %(university_id)s")
            params["university_id"] = UUID(university_id)
        if user_id:
            clauses.append("user_id = %(user_id)s")
            params["user_id"] = user_id
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT id, university_id, user_id, institutional_code, full_name,
                           document_number, email, person_type, status, created_at, updated_at
                    FROM persons
                    {where}
                    ORDER BY full_name
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._to_member_dict(row) for row in rows]

    def get_member(self, member_id: str) -> dict | None:
        return self._get_member_by(id=member_id)

    def get_member_by_user_id(self, user_id: str) -> dict | None:
        return self._get_member_by(user_id=user_id)

    def _get_member_by(self, **filters: str) -> dict | None:
        column, value = next(iter(filters.items()))
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT id, university_id, user_id, institutional_code, full_name,
                           document_number, email, person_type, status, created_at, updated_at
                    FROM persons
                    WHERE {column} = %(value)s
                    """,
                    {"value": UUID(value) if column == "id" else value},
                )
                row = cursor.fetchone()
        return None if row is None else self._to_member_dict(row)

    # ------------------------------------------------------------------ #
    # Vehiculos (vehicles)
    # ------------------------------------------------------------------ #
    def get_vehicles_for_person(self, person_id: str) -> list[dict]:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT v.id, v.university_id, v.plate, v.brand, v.model, v.color,
                                    v.status, v.created_at, v.updated_at
                    FROM vehicles v
                    JOIN vehicle_authorizations a ON a.vehicle_id = v.id
                    WHERE a.person_id = %(person_id)s
                    ORDER BY v.plate
                    """,
                    {"person_id": UUID(person_id)},
                )
                rows = cursor.fetchall()
        return [self._to_vehicle_dict(row) for row in rows]

    def create_vehicle(self, payload: dict) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO vehicles (id, university_id, plate, brand, model, color, status)
                    VALUES (gen_random_uuid(), %(university_id)s, %(plate)s, %(brand)s, %(model)s, %(color)s, %(status)s)
                    RETURNING id, university_id, plate, brand, model, color, status, created_at, updated_at
                    """,
                    {
                        "university_id": UUID(payload["university_id"]),
                        "plate": self.normalize_plate(payload["plate_text"]),
                        "brand": payload["brand"],
                        "model": payload["model"],
                        "color": payload["color"],
                        "status": payload.get("status", "ACTIVE").lower(),
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._to_vehicle_dict(row)

    def list_vehicles(self, university_id: str | None = None) -> list[dict]:
        clause = "WHERE university_id = %(university_id)s" if university_id else ""
        params = {"university_id": UUID(university_id)} if university_id else {}
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT id, university_id, plate, brand, model, color, status, created_at, updated_at
                    FROM vehicles
                    {clause}
                    ORDER BY plate
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._to_vehicle_dict(row) for row in rows]

    def get_vehicle(self, vehicle_id: str) -> dict | None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, university_id, plate, brand, model, color, status, created_at, updated_at
                    FROM vehicles WHERE id = %(id)s
                    """,
                    {"id": UUID(vehicle_id)},
                )
                row = cursor.fetchone()
        return None if row is None else self._to_vehicle_dict(row)

    def update_vehicle(self, vehicle_id: str, payload: dict) -> dict | None:
        fields: dict[str, Any] = {}
        if payload.get("plate_text"):
            fields["plate"] = self.normalize_plate(payload["plate_text"])
        for field in ("brand", "model", "color"):
            if payload.get(field):
                fields[field] = payload[field]
        if not fields:
            return self.get_vehicle(vehicle_id)
        assignments = ", ".join(f"{column} = %({column})s" for column in fields)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    UPDATE vehicles SET {assignments}
                    WHERE id = %(id)s
                    RETURNING id, university_id, plate, brand, model, color, status, created_at, updated_at
                    """,
                    {**fields, "id": UUID(vehicle_id)},
                )
                row = cursor.fetchone()
            connection.commit()
        return None if row is None else self._to_vehicle_dict(row)

    def get_vehicle_by_plate(self, plate_text: str) -> dict | None:
        normalized = self.normalize_plate(plate_text)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, university_id, plate, brand, model, color, status, created_at, updated_at
                    FROM vehicles WHERE plate = %(plate)s
                    """,
                    {"plate": normalized},
                )
                row = cursor.fetchone()
        return None if row is None else self._to_vehicle_dict(row)

    # ------------------------------------------------------------------ #
    # Autorizaciones (vehicle_authorizations)
    # ------------------------------------------------------------------ #
    def authorize_person(self, vehicle_id: str, person_id: str, is_owner: bool, status: str = "ACTIVE") -> dict:
        vehicle = self.get_vehicle(vehicle_id)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO vehicle_authorizations (
                        id, university_id, vehicle_id, person_id, authorization_type, valid_from, status
                    )
                    VALUES (
                        gen_random_uuid(), %(university_id)s, %(vehicle_id)s, %(person_id)s,
                        %(authorization_type)s, NOW(), %(status)s
                    )
                    ON CONFLICT (university_id, vehicle_id, person_id, authorization_type)
                    DO UPDATE SET status = EXCLUDED.status
                    RETURNING id, university_id, person_id, vehicle_id, authorization_type, status, created_at, updated_at
                    """,
                    {
                        "university_id": UUID(vehicle["university_id"]),
                        "vehicle_id": UUID(vehicle_id),
                        "person_id": UUID(person_id),
                        "authorization_type": "owner" if is_owner else "authorized_driver",
                        "status": status.lower(),
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._to_authorization_dict(row)

    def get_authorized_people_for_vehicle(self, vehicle_id: str) -> list[dict]:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT p.id, p.university_id, p.user_id, p.institutional_code, p.full_name,
                           p.document_number, p.email, p.person_type, p.status, p.created_at, p.updated_at,
                           a.id AS authorization_id, a.authorization_type
                    FROM vehicle_authorizations a
                    JOIN persons p ON p.id = a.person_id
                    WHERE a.vehicle_id = %(vehicle_id)s
                      AND a.status = 'active'
                      AND p.status = 'active'
                    ORDER BY (a.authorization_type != 'owner'), p.full_name
                    """,
                    {"vehicle_id": UUID(vehicle_id)},
                )
                rows = cursor.fetchall()
        items = []
        for row in rows:
            member = self._to_member_dict(row)
            member["is_owner"] = row["authorization_type"] == "owner"
            member["authorization_id"] = str(row["authorization_id"])
            items.append(member)
        return items

    # ------------------------------------------------------------------ #
    # Perfiles de rostro (indice; embeddings reales viven en face-service)
    # ------------------------------------------------------------------ #
    def create_face_profile(self, payload: dict) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO face_profiles (
                        id, university_id, person_id, face_image_id, template_id, embedding_id, provider, status
                    )
                    VALUES (
                        gen_random_uuid(), %(university_id)s, %(person_id)s, %(face_image_id)s,
                        %(template_id)s, %(template_id)s, %(provider)s, %(status)s
                    )
                    RETURNING id, university_id, person_id, face_image_id, template_id, embedding_id,
                              provider, status, created_at, updated_at
                    """,
                    {
                        "university_id": UUID(payload["university_id"]),
                        "person_id": UUID(payload["person_id"]),
                        "face_image_id": UUID(payload["face_image_id"]),
                        "template_id": UUID(payload["template_id"]),
                        "provider": payload["provider"],
                        "status": payload.get("status", "ACTIVE").upper(),
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._to_face_profile_dict(row)

    def list_face_profiles(self, university_id: str | None = None) -> list[dict]:
        clause = "WHERE university_id = %(university_id)s" if university_id else ""
        params = {"university_id": UUID(university_id)} if university_id else {}
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT id, university_id, person_id, face_image_id, template_id, embedding_id,
                           provider, status, created_at, updated_at
                    FROM face_profiles
                    {clause}
                    ORDER BY created_at DESC
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._to_face_profile_dict(row) for row in rows]

    def get_face_profiles_by_person(self, person_id: str) -> list[dict]:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, university_id, person_id, face_image_id, template_id, embedding_id,
                           provider, status, created_at, updated_at
                    FROM face_profiles
                    WHERE person_id = %(person_id)s AND status = 'ACTIVE'
                    ORDER BY created_at DESC
                    """,
                    {"person_id": UUID(person_id)},
                )
                rows = cursor.fetchall()
        return [self._to_face_profile_dict(row) for row in rows]

    # ------------------------------------------------------------------ #
    # Permisos mensuales (monthly_permits)
    # ------------------------------------------------------------------ #
    def create_monthly_permit(self, payload: dict) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                receipt_number = payload.get("receipt_number")
                if not receipt_number:
                    cursor.execute("SELECT nextval('monthly_permits_receipt_seq') AS seq")
                    seq = cursor.fetchone()["seq"]
                    receipt_number = f"MEM-{datetime.now(UTC):%Y%m%d}-{seq:04d}"
                cursor.execute(
                    """
                    INSERT INTO monthly_permits (
                        id, university_id, person_id, vehicle_id, start_date, end_date,
                        amount, payment_method, status, paid_at, receipt_number
                    )
                    VALUES (
                        gen_random_uuid(), %(university_id)s, %(person_id)s, %(vehicle_id)s,
                        %(start_date)s, %(end_date)s, %(amount)s, %(payment_method)s, %(status)s,
                        %(paid_at)s, %(receipt_number)s
                    )
                    RETURNING id, university_id, person_id, vehicle_id, start_date, end_date,
                              amount, payment_method, status, paid_at, receipt_number, created_at, updated_at
                    """,
                    {
                        "university_id": UUID(payload["university_id"]),
                        "person_id": UUID(payload["person_id"]),
                        "vehicle_id": UUID(payload["vehicle_id"]),
                        "start_date": payload["start_date"],
                        "end_date": payload["end_date"],
                        "amount": round(float(payload["amount"]), 2),
                        "payment_method": payload["payment_method"],
                        "status": payload.get("status", "VALID"),
                        "paid_at": payload.get("paid_at") or datetime.now(UTC),
                        "receipt_number": receipt_number,
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._to_permit_dict(row)

    def list_monthly_permits(self, university_id: str | None = None) -> list[dict]:
        clause = "WHERE university_id = %(university_id)s" if university_id else ""
        params = {"university_id": UUID(university_id)} if university_id else {}
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    SELECT id, university_id, person_id, vehicle_id, start_date, end_date,
                           amount, payment_method, status, paid_at, receipt_number, created_at, updated_at
                    FROM monthly_permits
                    {clause}
                    ORDER BY created_at DESC
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [self._to_permit_dict(row) for row in rows]

    def get_valid_permit(self, *, person_id: str, vehicle_id: str) -> dict | None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, university_id, person_id, vehicle_id, start_date, end_date,
                           amount, payment_method, status, paid_at, receipt_number, created_at, updated_at
                    FROM monthly_permits
                    WHERE person_id = %(person_id)s AND vehicle_id = %(vehicle_id)s
                      AND status = 'VALID' AND start_date <= %(today)s AND end_date >= %(today)s
                    ORDER BY end_date DESC
                    LIMIT 1
                    """,
                    {"person_id": UUID(person_id), "vehicle_id": UUID(vehicle_id), "today": date.today()},
                )
                row = cursor.fetchone()
        return None if row is None else self._to_permit_dict(row)

    def get_permit_by_plate(self, plate_text: str) -> dict | None:
        vehicle = self.get_vehicle_by_plate(plate_text)
        if vehicle is None:
            return None
        for person in self.get_authorized_people_for_vehicle(vehicle["id"]):
            permit = self.get_valid_permit(person_id=person["id"], vehicle_id=vehicle["id"])
            if permit:
                permit["person_name"] = person["full_name"]
                permit["role_type"] = person["role_type"]
                permit["plate_text"] = vehicle["plate_text"]
                return permit
        return None

    @staticmethod
    def normalize_plate(plate_text: str) -> str:
        return str(plate_text or "").strip().upper().replace(" ", "").replace("-", "")

    # ------------------------------------------------------------------ #
    def _ensure_seed_data(self) -> None:
        university_id = UUID(self.UNIVERSITY_ID)
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                person_ids: dict[str, UUID] = {}
                for seed in _SEED_MEMBERS:
                    cursor.execute(
                        """
                        INSERT INTO persons (
                            id, university_id, institutional_code, full_name,
                            document_number, email, person_type, status
                        )
                        VALUES (
                            gen_random_uuid(), %(university_id)s, %(institutional_id)s, %(full_name)s,
                            %(document_id)s, %(email)s, %(person_type)s, 'active'
                        )
                        ON CONFLICT (university_id, document_number) DO UPDATE SET full_name = EXCLUDED.full_name
                        RETURNING id
                        """,
                        {
                            "university_id": university_id,
                            "institutional_id": seed["institutional_id"],
                            "full_name": seed["full_name"],
                            "document_id": seed["document_id"],
                            "email": seed["email"],
                            "person_type": ROLE_TYPE_TO_PERSON_TYPE[seed["role_type"]],
                        },
                    )
                    person_ids[seed["document_id"]] = cursor.fetchone()["id"]

                vehicle_ids: dict[str, UUID] = {}
                for seed in _SEED_VEHICLES:
                    cursor.execute(
                        """
                        INSERT INTO vehicles (id, university_id, plate, brand, model, color, status)
                        VALUES (gen_random_uuid(), %(university_id)s, %(plate)s, %(brand)s, %(model)s, %(color)s, 'active')
                        ON CONFLICT (university_id, plate) DO UPDATE SET brand = EXCLUDED.brand
                        RETURNING id
                        """,
                        {
                            "university_id": university_id,
                            "plate": seed["plate_text"],
                            "brand": seed["brand"],
                            "model": seed["model"],
                            "color": seed["color"],
                        },
                    )
                    vehicle_ids[seed["plate_text"]] = cursor.fetchone()["id"]

                for document_id, plate_text, is_owner in _SEED_AUTHORIZATIONS:
                    cursor.execute(
                        """
                        INSERT INTO vehicle_authorizations (
                            id, university_id, vehicle_id, person_id, authorization_type, valid_from, status
                        )
                        VALUES (
                            gen_random_uuid(), %(university_id)s, %(vehicle_id)s, %(person_id)s,
                            %(authorization_type)s, NOW(), 'active'
                        )
                        ON CONFLICT (university_id, vehicle_id, person_id, authorization_type) DO NOTHING
                        """,
                        {
                            "university_id": university_id,
                            "vehicle_id": vehicle_ids[plate_text],
                            "person_id": person_ids[document_id],
                            "authorization_type": "owner" if is_owner else "authorized_driver",
                        },
                    )

                for document_id, plate_text, start_offset, end_offset, amount, method, status, receipt in _SEED_PERMITS:
                    cursor.execute(
                        """
                        INSERT INTO monthly_permits (
                            id, university_id, person_id, vehicle_id, start_date, end_date,
                            amount, payment_method, status, paid_at, receipt_number
                        )
                        VALUES (
                            gen_random_uuid(), %(university_id)s, %(person_id)s, %(vehicle_id)s,
                            CURRENT_DATE + %(start_offset)s, CURRENT_DATE + %(end_offset)s,
                            %(amount)s, %(method)s, %(status)s, NOW(), %(receipt)s
                        )
                        ON CONFLICT (receipt_number) DO NOTHING
                        """,
                        {
                            "university_id": university_id,
                            "person_id": person_ids[document_id],
                            "vehicle_id": vehicle_ids[plate_text],
                            "start_offset": start_offset,
                            "end_offset": end_offset,
                            "amount": amount,
                            "method": method,
                            "status": status,
                            "receipt": receipt,
                        },
                    )

                for document_id, provider in _SEED_FACE_PROFILES:
                    cursor.execute(
                        "SELECT 1 FROM face_profiles WHERE person_id = %(person_id)s",
                        {"person_id": person_ids[document_id]},
                    )
                    if cursor.fetchone() is not None:
                        continue
                    cursor.execute(
                        """
                        INSERT INTO face_profiles (
                            id, university_id, person_id, face_image_id, template_id, embedding_id, provider, status
                        )
                        VALUES (
                            gen_random_uuid(), %(university_id)s, %(person_id)s, gen_random_uuid(),
                            gen_random_uuid(), gen_random_uuid(), %(provider)s, 'ACTIVE'
                        )
                        """,
                        {
                            "university_id": university_id,
                            "person_id": person_ids[document_id],
                            "provider": provider,
                        },
                    )
            connection.commit()

    def _to_member_dict(self, row: dict[str, Any]) -> dict:
        return {
            "id": str(row["id"]),
            "university_id": str(row["university_id"]),
            "document_id": row["document_number"],
            "institutional_id": row["institutional_code"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role_type": PERSON_TYPE_TO_ROLE_TYPE.get(row["person_type"], row["person_type"].upper()),
            "status": row["status"].upper(),
            "user_id": row.get("user_id"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _to_vehicle_dict(self, row: dict[str, Any]) -> dict:
        return {
            "id": str(row["id"]),
            "university_id": str(row["university_id"]),
            "plate_text": row["plate"],
            "brand": row["brand"],
            "model": row["model"],
            "color": row["color"],
            "status": row["status"].upper(),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _to_authorization_dict(self, row: dict[str, Any]) -> dict:
        return {
            "id": str(row["id"]),
            "university_id": str(row["university_id"]),
            "person_id": str(row["person_id"]),
            "vehicle_id": str(row["vehicle_id"]),
            "is_owner": row["authorization_type"] == "owner",
            "status": row["status"].upper(),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _to_face_profile_dict(self, row: dict[str, Any]) -> dict:
        return {
            "id": str(row["id"]),
            "university_id": str(row["university_id"]),
            "person_id": str(row["person_id"]),
            "face_image_id": str(row["face_image_id"]),
            "template_id": str(row["template_id"]),
            "embedding_id": str(row["embedding_id"]),
            "provider": row["provider"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _to_permit_dict(self, row: dict[str, Any]) -> dict:
        return {
            "id": str(row["id"]),
            "university_id": str(row["university_id"]),
            "person_id": str(row["person_id"]),
            "vehicle_id": str(row["vehicle_id"]),
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "amount": float(row["amount"]),
            "payment_method": row["payment_method"],
            "status": row["status"],
            "paid_at": row.get("paid_at"),
            "receipt_number": row.get("receipt_number"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
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
                    "member_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
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
