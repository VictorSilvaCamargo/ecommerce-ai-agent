import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Atendente IA - NovaLoja"
    environment: str = "development"
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    api_key: str = "nova-loja-secret-api-key-test"
    webhook_secret: str = "supersecret-hmac-webhook-key-32chars"

    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://novaloja:novalojapass@localhost:5432/novaloja_db"
    )
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://root:mongopass@localhost:27017/")
    mongodb_database: str = "novaloja_audit"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
