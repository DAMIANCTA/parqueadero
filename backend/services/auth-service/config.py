from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "auth-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    cors_allow_origins_csv: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")
    jwt_secret_key: str = ""
    jwt_issuer: str = "smart-parking-university"
    jwt_audience: str = "smart-parking-clients"
    jwt_access_token_expires_minutes: int = 60
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    audit_enabled: bool = True
    audit_service_url: str = "http://audit-service:8000"
    audit_internal_key: str = ""
    postgres_core_host: str = "postgres-core"
    postgres_core_internal_port: int = 5432
    postgres_core_db: str = "parking_core"
    postgres_core_user: str = "parking_user"
    postgres_core_password: str = "parking_pass"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_allow_origins(self) -> list[str]:
        values = [value.strip() for value in self.cors_allow_origins_csv.split(",") if value.strip()]
        return values or ["*"]


settings = Settings()
