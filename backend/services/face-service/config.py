from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "face-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    face_service_mode: str = "mock"
    face_real_provider: str = "insightface"
    face_similarity_threshold: float = 0.82
    face_liveness_threshold: float = 0.75
    face_embedding_dimensions: int = 16
    face_default_bucket: str = "parking-raw-images"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
