class VehicleAuthorizationRepository:
    def __init__(self) -> None:
        self.authorizations = {
            "ABC1234": {"student", "teacher", "employee"},
            "XYZ9876": {"teacher", "employee"},
            "EMP2026": {"employee"},
        }

    def validate_plate_authorization(self, university_id: str, plate_text: str, person_type: str) -> dict:
        del university_id
        allowed_person_types = self.authorizations.get(plate_text, set())
        return {
            "authorized": person_type in allowed_person_types,
            "allowed_person_types": sorted(allowed_person_types),
        }
