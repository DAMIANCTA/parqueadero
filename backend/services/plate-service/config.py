from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "plate-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    plate_service_mode: str = "mock"
    plate_default_country_code: str = "EC"
    plate_min_confidence: float = 0.70

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
