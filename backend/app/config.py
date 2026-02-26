from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "PickRank API"
    debug: bool = False
    environment: str = "development"
    secret_key: str = "change-me"
    allowed_origins: str = "http://localhost:3000"

    # Supabase direct connection – used by Alembic migrations only
    database_url: str = ""

    # Supabase Transaction Pooler – used by the app / Vercel serverless
    database_pool_url: str = ""

    # OpenAI (Phase 2)
    openai_api_key: str = ""

    # Market Data (Phase 3)
    polygon_api_key: str = ""
    alpha_vantage_api_key: str = ""

    # YouTube (Phase 2)
    youtube_api_key: str = ""

    # SendGrid (Phase 5)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@pickrank.io"

    # Sentry (Phase 5)
    sentry_dsn: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def active_database_url(self) -> str:
        """Return the pooler URL for the app; fall back to direct URL."""
        return self.database_pool_url or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
