from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str
    api_host: str
    api_port: int
    cors_origins: str

    # Optional MQTT broker, e.g. mqtt://localhost:1883. When unset, the
    # MQTT subscriber is not started and nothing connects to a broker.
    mqtt_broker_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()