from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5433/ad_moderation"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_moderation_topic: str = "moderation"
    kafka_dlq_topic: str = "moderation_dlq"
    worker_max_retries: int = 3
    worker_retry_delay_seconds: int = 5

    @property
    def database_dsn(self) -> str:
        return self.database_url.split("?")[0]
