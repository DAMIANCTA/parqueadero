from uuid import uuid4


class AuditRepository:
    _events: list[dict] = []

    @classmethod
    def add_event(cls, payload: dict) -> dict:
        record = {"id": str(uuid4()), **payload}
        cls._events.append(record)
        return record

    @classmethod
    def list_events(cls, limit: int) -> list[dict]:
        return list(reversed(cls._events[-limit:]))
