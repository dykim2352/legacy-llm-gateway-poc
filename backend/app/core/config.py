from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Legacy 연동 LLM Gateway PoC"
    app_version: str = "0.1.0"
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://llm:llm@postgres:5432/llm_gateway"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    cache_ttl_seconds: int = 300
    legacy_service_base_url: str = "http://legacy-mock-service:8081"
    jwt_secret: str = "local-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    llm_request_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
