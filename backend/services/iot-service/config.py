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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
