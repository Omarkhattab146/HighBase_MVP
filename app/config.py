from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "HIGHBASE Recommendation AI"
    app_version: str = "0.1.0"
    mongo_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "highbase_mvp"
    storage_backend: str = "json"
    data_path: str = "data"
    pipeline_version: str = "2026.08.1"
    llm_api_key: str | None = None
    llm_model: str = "qwen3:8b"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_timeout_seconds: float = 1.0
    chat_session_ttl_seconds: int = 1800
    chat_max_history: int = 12
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
