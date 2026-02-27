from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    open_api_key: str = ""
    database_url: str = ""
    model_id: str = "gpt-4o-mini"
    embedding_model_id: str = "text-embedding-3-small"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        # Normalise legacy "postgres://" scheme (SQLAlchemy 2.x requires "postgresql://").
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]

        # Pin the psycopg3 driver (used by langchain_postgres). Without this,
        # SQLAlchemy may pick asyncpg which requires an async context.
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]

        return v


settings = Settings()
