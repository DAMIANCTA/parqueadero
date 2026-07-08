from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "face-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    face_service_mode: str = "hybrid"
    face_real_provider: str = "insightface"
    face_similarity_threshold: float = 0.82
    face_liveness_threshold: float = 0.75
    face_embedding_dimensions: int = 512
    face_default_bucket: str = "parking-faces"
    face_detector_confidence_threshold: float = 0.35
    face_quality_threshold: float = 0.45
    face_insightface_app_name: str = "buffalo_l"
    face_insightface_root: str = "/tmp/insightface"
    postgres_biometrics_host: str = "postgres-biometrics"
    postgres_biometrics_internal_port: int = 5432
    postgres_biometrics_db: str = "parking_biometrics"
    postgres_biometrics_user: str = "biometric_user"
    postgres_biometrics_password: str = "biometric_pass"
    minio_internal_url: str = "http://minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin123"
    minio_bucket_faces: str = "parking-faces"
    jwt_secret_key: str = ""
    jwt_issuer: str = "smart-parking-university"
    jwt_audience: str = "smart-parking-clients"
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    audit_enabled: bool = True
    audit_service_url: str = "http://audit-service:8000"
    audit_internal_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
