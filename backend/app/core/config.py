from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Required
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str = ""  # empty = Supabase JWKS (ES256/RS256)
    gmail_client_id: str
    gmail_client_secret: str
    gmail_redirect_uri: str
    oauth_state_secret: str
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""
    frontend_url: str

    # Optional with defaults
    environment: str = "dev"
    log_level: str = "INFO"
    allowed_origins: str = ""  # comma-separated; empty → derive from frontend_url
    sentry_dsn: str | None = None
    git_sha: str = "dev"
    demo_mode: bool = False  # seed sample emails when a Gmail account connects

    # Secrets whose presence is not reported in startup logs.
    _UNREPORTED: tuple[str, ...] = ("supabase_service_role_key",)

    def presence_summary(self) -> dict[str, bool]:
        """Which string settings are populated. Safe to log: contains no values."""
        return {
            f"{name}_set": bool(value)
            for name, value in self.model_dump().items()
            if not isinstance(value, bool) and name not in self._UNREPORTED
        }

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        return list({self.frontend_url.rstrip("/"), "http://localhost:3000"})


settings = Settings()  # type: ignore[call-arg]
