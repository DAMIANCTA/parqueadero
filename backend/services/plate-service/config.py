from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "plate-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    plate_service_mode: str = "mock"
    plate_detection_mode: str = ""
    plate_default_country_code: str = "EC"
    plate_min_confidence: float = 0.70
    plate_auto_accept_confidence: float = 0.75
    minio_internal_url: str = "http://minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin123"
    postgres_biometrics_host: str = "postgres-biometrics"
    postgres_biometrics_internal_port: int = 5432
    postgres_biometrics_db: str = "parking_biometrics"
    postgres_biometrics_user: str = "biometric_user"
    postgres_biometrics_password: str = "biometric_pass"
    jwt_secret_key: str = ""
    jwt_issuer: str = "smart-parking-university"
    jwt_audience: str = "smart-parking-clients"
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    audit_enabled: bool = True
    audit_service_url: str = "http://audit-service:8000"
    audit_internal_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def effective_plate_detection_mode(self) -> str:
        return (self.plate_detection_mode or self.plate_service_mode or "mock").strip().lower()


settings = Settings()
