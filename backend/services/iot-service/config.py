from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "iot-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883
    mqtt_qos: int = 0
    mqtt_keepalive: int = 60
    mqtt_username: str | None = None
    mqtt_password: str | None = None
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
