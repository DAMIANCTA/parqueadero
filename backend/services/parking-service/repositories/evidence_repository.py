from datetime import datetime, timezone
from uuid import uuid4


class EvidenceRepository:
    evidence_records: dict[str, dict] = {}

    def create_reference(
        self,
        *,
        bucket: str,
        object_name: str,
        image_type: str,
        plate: str,
        session_id: str | None = None,
    ) -> dict:
        image_id = str(uuid4())
        record = {
            "image_id": image_id,
            "bucket": bucket,
            "object_name": object_name,
            "image_type": image_type,
            "session_id": session_id,
            "plate": plate,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        self.evidence_records[image_id] = record
        return record.copy()

    def link_to_session(self, image_id: str, session_id: str, plate: str) -> dict | None:
        record = self.evidence_records.get(image_id)
        if record is None:
            return None
        record["session_id"] = session_id
        record["plate"] = plate
        self.evidence_records[image_id] = record
        return record.copy()

    def get(self, image_id: str) -> dict | None:
        record = self.evidence_records.get(image_id)
        return None if record is None else record.copy()
