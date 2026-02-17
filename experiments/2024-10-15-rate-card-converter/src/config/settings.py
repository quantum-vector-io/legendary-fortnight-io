"""Application settings loaded from environment variables and .env file.

Uses pydantic-settings for type-safe configuration with automatic environment
variable parsing. The get_settings() function is decorated with lru_cache to
ensure only one Settings instance is created per process lifetime, preventing
repeated disk reads on every Depends() call in FastAPI.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration sourced from environment variables.

    All fields have defaults suitable for local development. Production and
    Azure deployments override values through environment variables or a .env
    file. The ENVIRONMENT field governs which infrastructure adapters are
    selected by the dependency injection container.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Runtime environment — controls which adapters are injected.
    environment: str = Field(default="local", description="Runtime environment: local or azure.")

    # OpenAI configuration.
    openai_api_key: str = Field(default="sk-mock-key", description="OpenAI API key.")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model identifier.")
    openai_max_tokens: int = Field(default=2048, description="Maximum tokens for LLM output.")
    openai_temperature: float = Field(default=0.0, description="Sampling temperature (0 = deterministic).")

    # Database — SQLite for local, PostgreSQL for Azure.
    database_url: str = Field(
        default="sqlite+aiosqlite:///./rate_cards.db",
        description="SQLAlchemy async database connection string.",
    )

    # File upload storage directory.
    upload_dir: str = Field(default="./uploads", description="Directory for uploaded document storage.")

    # Logging.
    log_level: str = Field(default="INFO", description="Python logging level.")

    # Azure Document Intelligence — only required when ENVIRONMENT=azure.
    azure_document_intelligence_endpoint: str = Field(
        default="",
        description="Azure Document Intelligence endpoint URL.",
    )
    azure_document_intelligence_key: str = Field(
        default="",
        description="Azure Document Intelligence API key.",
    )

    # Redis — only required when ENVIRONMENT=azure.
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery broker.",
    )

    # PostgreSQL — alternative to DATABASE_URL for Azure deployments.
    postgres_url: str = Field(
        default="",
        description="PostgreSQL async connection string (overrides DATABASE_URL in Azure).",
    )

    @property
    def is_local(self) -> bool:
        """Return True when running in local development mode.

        Returns:
            True if ENVIRONMENT is set to 'local', False otherwise.
        """
        return self.environment.lower() == "local"

    @property
    def use_azure_document_extractor(self) -> bool:
        """Return True when Azure Document Intelligence should be used.

        The Azure extractor is activated only when ENVIRONMENT=azure and
        the endpoint and key are both configured.

        Returns:
            True if Azure Document Intelligence credentials are present and
            the environment is not local.
        """
        return (
            not self.is_local
            and bool(self.azure_document_intelligence_endpoint)
            and bool(self.azure_document_intelligence_key)
        )

    @property
    def effective_database_url(self) -> str:
        """Return the database URL to use, preferring POSTGRES_URL in Azure mode.

        Returns:
            The configured PostgreSQL URL when running in Azure mode and
            postgres_url is set, otherwise the standard DATABASE_URL.
        """
        if not self.is_local and self.postgres_url:
            return self.postgres_url
        return self.database_url


@lru_cache()
def get_settings() -> Settings:
    """Return the application settings singleton.

    The result is cached after the first call to avoid repeated .env file
    reads. In tests, clear the cache with get_settings.cache_clear() before
    injecting test-specific settings.

    Returns:
        The application Settings instance.
    """
    return Settings()
