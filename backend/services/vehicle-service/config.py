from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "vehicle-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    face_service_url: str = "http://face-service:8000"
    face_service_timeout_seconds: float = 10.0
    face_similarity_threshold: float = 0.82
    postgres_biometrics_host: str = "postgres-biometrics"
    postgres_biometrics_internal_port: int = 5432
    postgres_biometrics_db: str = "parking_biometrics"
    postgres_biometrics_user: str = "biometric_user"
    postgres_biometrics_password: str = "biometric_pass"
    jwt_secret_key: str = ""
    jwt_issuer: str = "smart-parking-university"
    jwt_audience: str = "smart-parking-clients"
    jwt_access_token_expires_minutes: int = 60
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    audit_enabled: bool = True
    audit_service_url: str = "http://audit-service:8000"
    audit_internal_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
