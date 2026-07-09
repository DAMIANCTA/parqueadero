import uuid
from copy import deepcopy
from datetime import UTC, date, datetime, timedelta


class MemberRepository:
    UNIVERSITY_ID = "11111111-1111-1111-1111-111111111111"

    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.members = getattr(
            self.__class__,
            "_members",
            {
                "person-student-001": {
                    "id": "person-student-001",
                    "university_id": self.UNIVERSITY_ID,
                    "document_id": "0102030405",
                    "institutional_id": "UCE2026001",
                    "full_name": "Ana Belen Torres",
                    "email": "ana.torres@uce.edu.ec",
                    "role_type": "STUDENT",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "person-teacher-001": {
                    "id": "person-teacher-001",
                    "university_id": self.UNIVERSITY_ID,
                    "document_id": "1112131415",
                    "institutional_id": "UCE-DOC-100",
                    "full_name": "Carlos Mena",
                    "email": "carlos.mena@uce.edu.ec",
                    "role_type": "TEACHER",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "person-staff-001": {
                    "id": "person-staff-001",
                    "university_id": self.UNIVERSITY_ID,
                    "document_id": "1617181920",
                    "institutional_id": "UCE-ADM-050",
                    "full_name": "Maria Fernanda Ruiz",
                    "email": "maria.ruiz@uce.edu.ec",
                    "role_type": "STAFF",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
            },
        )
        self.vehicles = getattr(
            self.__class__,
            "_vehicles",
            {
                "vehicle-001": {
                    "id": "vehicle-001",
                    "university_id": self.UNIVERSITY_ID,
                    "plate_text": "ABC1234",
                    "brand": "Chevrolet",
                    "model": "Spark",
                    "color": "Rojo",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "vehicle-002": {
                    "id": "vehicle-002",
                    "university_id": self.UNIVERSITY_ID,
                    "plate_text": "XYZ9876",
                    "brand": "Kia",
                    "model": "Rio",
                    "color": "Blanco",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "vehicle-003": {
                    "id": "vehicle-003",
                    "university_id": self.UNIVERSITY_ID,
                    "plate_text": "EMP2026",
                    "brand": "Hyundai",
                    "model": "Accent",
                    "color": "Gris",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "vehicle-004": {
                    "id": "vehicle-004",
                    "university_id": self.UNIVERSITY_ID,
                    "plate_text": "EXP2026",
                    "brand": "Nissan",
                    "model": "Versa",
                    "color": "Azul",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
            },
        )
        self.authorizations = getattr(
            self.__class__,
            "_authorizations",
            {
                "auth-001": {
                    "id": "auth-001",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-student-001",
                    "vehicle_id": "vehicle-001",
                    "is_owner": True,
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "auth-002": {
                    "id": "auth-002",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-teacher-001",
                    "vehicle_id": "vehicle-002",
                    "is_owner": True,
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "auth-003": {
                    "id": "auth-003",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-staff-001",
                    "vehicle_id": "vehicle-003",
                    "is_owner": True,
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "auth-004": {
                    "id": "auth-004",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-staff-001",
                    "vehicle_id": "vehicle-004",
                    "is_owner": False,
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
            },
        )
        self.permits = getattr(
            self.__class__,
            "_permits",
            {
                "permit-001": {
                    "id": "permit-001",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-student-001",
                    "vehicle_id": "vehicle-001",
                    "start_date": date.today() - timedelta(days=7),
                    "end_date": date.today() + timedelta(days=23),
                    "amount": 15.0,
                    "payment_method": "transfer",
                    "status": "VALID",
                    "paid_at": now - timedelta(days=2),
                    "receipt_number": "MEM-202607-001",
                    "created_at": now,
                    "updated_at": now,
                },
                "permit-002": {
                    "id": "permit-002",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-teacher-001",
                    "vehicle_id": "vehicle-002",
                    "start_date": date.today() - timedelta(days=4),
                    "end_date": date.today() + timedelta(days=26),
                    "amount": 20.0,
                    "payment_method": "cash",
                    "status": "VALID",
                    "paid_at": now - timedelta(days=1),
                    "receipt_number": "MEM-202607-002",
                    "created_at": now,
                    "updated_at": now,
                },
                "permit-003": {
                    "id": "permit-003",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-staff-001",
                    "vehicle_id": "vehicle-004",
                    "start_date": date.today() - timedelta(days=40),
                    "end_date": date.today() - timedelta(days=10),
                    "amount": 20.0,
                    "payment_method": "cash",
                    "status": "EXPIRED",
                    "paid_at": now - timedelta(days=35),
                    "receipt_number": "MEM-202606-010",
                    "created_at": now,
                    "updated_at": now,
                },
            },
        )
        self.face_profiles = getattr(
            self.__class__,
            "_face_profiles",
            {
                "face-profile-001": {
                    "id": "face-profile-001",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-student-001",
                    "face_image_id": "face-student-001",
                    "template_id": "template-student-001",
                    "embedding_id": "template-student-001",
                    "provider": "mock-face-service",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "face-profile-002": {
                    "id": "face-profile-002",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-teacher-001",
                    "face_image_id": "face-teacher-001",
                    "template_id": "template-teacher-001",
                    "embedding_id": "template-teacher-001",
                    "provider": "mock-face-service",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
                "face-profile-003": {
                    "id": "face-profile-003",
                    "university_id": self.UNIVERSITY_ID,
                    "person_id": "person-staff-001",
                    "face_image_id": "face-staff-001",
                    "template_id": "template-staff-001",
                    "embedding_id": "template-staff-001",
                    "provider": "mock-face-service",
                    "status": "ACTIVE",
                    "created_at": now,
                    "updated_at": now,
                },
            },
        )
        self.__class__._members = self.members
        self.__class__._vehicles = self.vehicles
        self.__class__._authorizations = self.authorizations
        self.__class__._permits = self.permits
        self.__class__._face_profiles = self.face_profiles

    def create_member(self, payload: dict) -> dict:
        now = datetime.now(UTC)
        member_id = str(uuid.uuid4())
        record = {
            "id": member_id,
            "university_id": payload["university_id"],
            "document_id": payload["document_id"],
            "institutional_id": payload["institutional_id"],
            "full_name": payload["full_name"],
            "email": payload["email"],
            "role_type": payload["role_type"],
            "status": payload.get("status", "ACTIVE"),
            "created_at": now,
            "updated_at": now,
        }
        self.members[member_id] = record
        return deepcopy(record)

    def list_members(self, university_id: str | None = None) -> list[dict]:
        items = [deepcopy(item) for item in self.members.values()]
        if university_id:
            items = [item for item in items if item["university_id"] == university_id]
        items.sort(key=lambda item: item["full_name"])
        return items

    def get_member(self, member_id: str) -> dict | None:
        item = self.members.get(member_id)
        return deepcopy(item) if item else None

    def create_vehicle(self, payload: dict) -> dict:
        now = datetime.now(UTC)
        vehicle_id = str(uuid.uuid4())
        record = {
            "id": vehicle_id,
            "university_id": payload["university_id"],
            "plate_text": self.normalize_plate(payload["plate_text"]),
            "brand": payload["brand"],
            "model": payload["model"],
            "color": payload["color"],
            "status": payload.get("status", "ACTIVE"),
            "created_at": now,
            "updated_at": now,
        }
        self.vehicles[vehicle_id] = record
        return deepcopy(record)

    def list_vehicles(self, university_id: str | None = None) -> list[dict]:
        items = [deepcopy(item) for item in self.vehicles.values()]
        if university_id:
            items = [item for item in items if item["university_id"] == university_id]
        items.sort(key=lambda item: item["plate_text"])
        return items

    def get_vehicle(self, vehicle_id: str) -> dict | None:
        item = self.vehicles.get(vehicle_id)
        return deepcopy(item) if item else None

    def get_vehicle_by_plate(self, plate_text: str) -> dict | None:
        normalized = self.normalize_plate(plate_text)
        for item in self.vehicles.values():
            if item["plate_text"] == normalized:
                return deepcopy(item)
        return None

    def authorize_person(self, vehicle_id: str, person_id: str, is_owner: bool, status: str = "ACTIVE") -> dict:
        now = datetime.now(UTC)
        authorization_id = str(uuid.uuid4())
        vehicle = self.vehicles[vehicle_id]
        record = {
            "id": authorization_id,
            "university_id": vehicle["university_id"],
            "person_id": person_id,
            "vehicle_id": vehicle_id,
            "is_owner": bool(is_owner),
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        self.authorizations[authorization_id] = record
        return deepcopy(record)

    def get_authorized_people_for_vehicle(self, vehicle_id: str) -> list[dict]:
        items: list[dict] = []
        for authorization in self.authorizations.values():
            if authorization["vehicle_id"] != vehicle_id or authorization["status"] != "ACTIVE":
                continue
            person = self.members.get(authorization["person_id"])
            if not person or person["status"] != "ACTIVE":
                continue
            row = deepcopy(person)
            row["is_owner"] = authorization["is_owner"]
            row["authorization_id"] = authorization["id"]
            items.append(row)
        return sorted(items, key=lambda item: (not item["is_owner"], item["full_name"]))

    def create_face_profile(self, payload: dict) -> dict:
        now = datetime.now(UTC)
        profile_id = str(uuid.uuid4())
        record = {
            "id": profile_id,
            "university_id": payload["university_id"],
            "person_id": payload["person_id"],
            "face_image_id": payload["face_image_id"],
            "template_id": payload["template_id"],
            "embedding_id": payload["template_id"],
            "provider": payload["provider"],
            "status": payload.get("status", "ACTIVE"),
            "created_at": now,
            "updated_at": now,
        }
        self.face_profiles[profile_id] = record
        return deepcopy(record)

    def list_face_profiles(self, university_id: str | None = None) -> list[dict]:
        items = [deepcopy(item) for item in self.face_profiles.values()]
        if university_id:
            items = [item for item in items if item["university_id"] == university_id]
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items

    def get_face_profiles_by_person(self, person_id: str) -> list[dict]:
        items = [deepcopy(item) for item in self.face_profiles.values() if item["person_id"] == person_id and item["status"] == "ACTIVE"]
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items

    def create_monthly_permit(self, payload: dict) -> dict:
        now = datetime.now(UTC)
        permit_id = str(uuid.uuid4())
        record = {
            "id": permit_id,
            "university_id": payload["university_id"],
            "person_id": payload["person_id"],
            "vehicle_id": payload["vehicle_id"],
            "start_date": payload["start_date"],
            "end_date": payload["end_date"],
            "amount": round(float(payload["amount"]), 2),
            "payment_method": payload["payment_method"],
            "status": payload.get("status", "VALID"),
            "paid_at": payload.get("paid_at") or now,
            "receipt_number": payload.get("receipt_number") or f"MEM-{now.strftime('%Y%m%d')}-{len(self.permits) + 1:04d}",
            "created_at": now,
            "updated_at": now,
        }
        self.permits[permit_id] = record
        return deepcopy(record)

    def list_monthly_permits(self, university_id: str | None = None) -> list[dict]:
        items = [deepcopy(item) for item in self.permits.values()]
        if university_id:
            items = [item for item in items if item["university_id"] == university_id]
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items

    def get_valid_permit(self, *, person_id: str, vehicle_id: str) -> dict | None:
        today = date.today()
        valid_rows = []
        for permit in self.permits.values():
            if permit["person_id"] != person_id or permit["vehicle_id"] != vehicle_id:
                continue
            if permit["status"] != "VALID":
                continue
            if permit["start_date"] <= today <= permit["end_date"]:
                valid_rows.append(deepcopy(permit))
        valid_rows.sort(key=lambda item: item["end_date"], reverse=True)
        return valid_rows[0] if valid_rows else None

    def get_permit_by_plate(self, plate_text: str) -> dict | None:
        vehicle = self.get_vehicle_by_plate(plate_text)
        if vehicle is None:
            return None
        for person in self.get_authorized_people_for_vehicle(vehicle["id"]):
            permit = self.get_valid_permit(person_id=person["id"], vehicle_id=vehicle["id"])
            if permit:
                result = deepcopy(permit)
                result["person_name"] = person["full_name"]
                result["role_type"] = person["role_type"]
                result["plate_text"] = vehicle["plate_text"]
                return result
        return None

    @staticmethod
    def normalize_plate(plate_text: str) -> str:
        return str(plate_text or "").strip().upper().replace(" ", "").replace("-", "")
