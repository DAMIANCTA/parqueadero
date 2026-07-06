from repositories.evidence_reference_repository import EvidenceReferenceRepository
from repositories.minio_repository import MinioRepository
from services.image_payload import LoadedImagePayload


class MinioClientService:
    def __init__(self) -> None:
        self.evidence_repository = EvidenceReferenceRepository()
        self.minio_repository = MinioRepository()

    def download_image_from_minio(self, image_id: str) -> LoadedImagePayload:
        reference = self.evidence_repository.get_reference(image_id)
        if reference is None:
            raise LookupError(f"Image reference not found for {image_id}")

        bucket = reference.get("bucket")
        object_name = reference.get("object_name")
        if not bucket or not object_name:
            raise LookupError(f"Image reference {image_id} does not have a MinIO location")

        return self.minio_repository.load_registered_image(
            image_id=image_id,
            bucket=bucket,
            object_name=object_name,
        )
