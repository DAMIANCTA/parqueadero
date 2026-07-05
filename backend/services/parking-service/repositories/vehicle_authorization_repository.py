class VehicleAuthorizationRepository:
    def __init__(self) -> None:
        self.authorizations = {
            "ABC1234": {
                "allowed_person_types": {"student", "teacher", "employee"},
                "authorized_face_ids": {"face-student-001", "face-shared-001"},
                "permission_valid": True,
                "person_type": "student",
            },
            "XYZ9876": {
                "allowed_person_types": {"teacher", "employee"},
                "authorized_face_ids": {"face-teacher-001"},
                "permission_valid": True,
                "person_type": "teacher",
            },
            "EMP2026": {
                "allowed_person_types": {"employee"},
                "authorized_face_ids": {"face-employee-001"},
                "permission_valid": True,
                "person_type": "employee",
            },
            "EXP2026": {
                "allowed_person_types": {"employee"},
                "authorized_face_ids": {"face-expired-001"},
                "permission_valid": False,
                "person_type": "employee",
            },
        }

    def validate_plate_authorization(self, university_id: str, plate_text: str, person_type: str) -> dict:
        del university_id
        record = self.authorizations.get(plate_text)
        allowed_person_types = record["allowed_person_types"] if record else set()
        return {
            "authorized": person_type in allowed_person_types,
            "allowed_person_types": sorted(allowed_person_types),
        }

    def validate_registered_exit(self, university_id: str, plate_text: str, face_image_id: str) -> dict:
        del university_id
        record = self.authorizations.get(plate_text)
        if record is None:
            return {
                "plate_exists": False,
                "face_authorized": False,
                "permission_valid": False,
                "person_type": None,
            }

        return {
            "plate_exists": True,
            "face_authorized": face_image_id in record["authorized_face_ids"],
            "permission_valid": record["permission_valid"],
            "person_type": record["person_type"],
        }
