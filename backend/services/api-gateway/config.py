from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "api-gateway"
    service_version: str = "0.1.0"
    environment: str = "local"
    parking_service_url: str = "http://parking-service:8000"
    face_service_url: str = "http://face-service:8000"
    plate_service_url: str = "http://plate-service:8000"
    payment_service_url: str = "http://payment-service:8000"
    iot_service_url: str = "http://iot-service:8000"
    postgres_core_host: str = "postgres-core"
    postgres_core_internal_port: int = 5432
    postgres_core_db: str = "parking_core"
    postgres_core_user: str = "parking_user"
    postgres_core_password: str = "parking_pass"
    postgres_biometrics_host: str = "postgres-biometrics"
    postgres_biometrics_internal_port: int = 5432
    postgres_biometrics_db: str = "parking_biometrics"
    postgres_biometrics_user: str = "biometric_user"
    postgres_biometrics_password: str = "biometric_pass"
    minio_internal_url: str = "http://minio:9000"
    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883
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
