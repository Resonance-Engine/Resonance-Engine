"""Resonance Engine — Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Typed configuration loaded from environment variables / .env file."""

    # Database
    database_url: str = "postgresql+asyncpg://resonance:resonance@localhost:5432/resonance"
    redis_url: str = "redis://localhost:6379/0"

    # SEC EDGAR
    edgar_user_agent: str = "Resonance Engine team@resonance-engine.com"

    # Vector Store (Phase 1)
    pinecone_api_key: str = ""
    pinecone_index_name: str = "resonance-events"
    pinecone_environment: str = ""

    # Embeddings (Phase 1)
    openai_api_key: str = ""

    # Market Data (Phase 1)
    alpha_vantage_api_key: str = ""
    finnhub_api_key: str = ""

    # News (Phase 2)
    newsapi_key: str = ""
    gdelt_base_url: str = "https://api.gdeltproject.org/api/v2"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
