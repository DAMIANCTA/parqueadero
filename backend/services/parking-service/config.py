from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "parking-service"
    service_version: str = "0.1.0"
    environment: str = "local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
