from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    # Legacy HS256 only; leave empty when Supabase uses JWT Signing Keys (ECC / JWKS).
    supabase_jwt_secret: str = ""

    gmail_client_id: str
    gmail_client_secret: str
    gmail_redirect_uri: str

    frontend_url: str = "http://localhost:3000"
    openai_api_key: str = ""

    oauth_state_secret: str = ""

    @property
    def state_signing_key(self) -> str:
        # HMAC for Gmail OAuth state; service_role works when no legacy JWT secret is set.
        return (
            self.oauth_state_secret
            or self.supabase_jwt_secret
            or self.supabase_service_role_key
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
