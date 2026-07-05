from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "payment-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    fixed_first_hour_amount: float = 1.50
    additional_hour_amount: float = 0.75
    currency: str = "USD"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
