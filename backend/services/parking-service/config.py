from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "parking-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    min_liveness_score: float = 0.75
    min_face_confidence: float = 0.80
    min_plate_confidence: float = 0.80
    iot_service_url: str = "http://iot-service:8000"
    iot_service_timeout_seconds: float = 1.5
    payment_service_url: str = "http://payment-service:8000"
    payment_service_timeout_seconds: float = 1.5
    postgres_biometrics_host: str = "postgres-biometrics"
    postgres_biometrics_internal_port: int = 5432
    postgres_biometrics_db: str = "parking_biometrics"
    postgres_biometrics_user: str = "biometric_user"
    postgres_biometrics_password: str = "biometric_pass"
    minio_internal_url: str = "http://minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin123"
    minio_bucket_faces: str = "parking-faces"
    minio_bucket_plates: str = "parking-plates"
    minio_bucket_evidence: str = "parking-evidence"
    minio_bucket_temp: str = "parking-temp"
    jwt_secret_key: str = ""
    jwt_issuer: str = "smart-parking-university"
    jwt_audience: str = "smart-parking-clients"
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    audit_enabled: bool = True
    audit_service_url: str = "http://audit-service:8000"
    audit_internal_key: str = ""
    evidence_default_university_id: str = "00000000-0000-0000-0000-000000000001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
