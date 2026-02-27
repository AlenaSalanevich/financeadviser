from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    open_api_key: str = ""
    db_host: str = ""
    model_id: str = "gpt-4o-mini"
    embedding_model_id: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
