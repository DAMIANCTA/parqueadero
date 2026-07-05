from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "university-service"
    service_version: str = "0.1.0"
    environment: str = "local"
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
