from copy import deepcopy


class UserRepository:
    def __init__(self) -> None:
        self._users = {
            "super.admin": {
                "id": "user-superadmin-001",
                "username": "super.admin",
                "password": "demo1234!",
                "roles": ["superadmin"],
                "university_id": None,
            },
            "admin.university": {
                "id": "user-admin-university-001",
                "username": "admin.university",
                "password": "demo1234!",
                "roles": ["admin_university"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "security.agent": {
                "id": "user-security-001",
                "username": "security.agent",
                "password": "demo1234!",
                "roles": ["security"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "cashier.user": {
                "id": "user-cashier-001",
                "username": "cashier.user",
                "password": "demo1234!",
                "roles": ["cashier"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "gate.operator": {
                "id": "user-gate-001",
                "username": "gate.operator",
                "password": "demo1234!",
                "roles": ["gate_operator"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "student.user": {
                "id": "user-student-001",
                "username": "student.user",
                "password": "demo1234!",
                "roles": ["student"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "teacher.user": {
                "id": "user-teacher-001",
                "username": "teacher.user",
                "password": "demo1234!",
                "roles": ["teacher"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "employee.user": {
                "id": "user-employee-001",
                "username": "employee.user",
                "password": "demo1234!",
                "roles": ["employee"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
            "visitor.user": {
                "id": "user-visitor-001",
                "username": "visitor.user",
                "password": "demo1234!",
                "roles": ["visitor"],
                "university_id": None,
            },
            "auditor.user": {
                "id": "user-auditor-001",
                "username": "auditor.user",
                "password": "demo1234!",
                "roles": ["auditor"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
        }

    def get_user(self, username: str) -> dict | None:
        record = self._users.get(username)
        return deepcopy(record) if record else None
