from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # GitHub
    github_token: str = ""
    github_org: str = "bhapi-inc"
    github_repos: str = ""
    github_webhook_secret: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./bhapi.db"

    # Auth
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Redis (optional)
    redis_url: str = ""

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:8000"

    # SMTP (optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    @property
    def repo_list(self) -> list[str]:
        if not self.github_repos:
            return []
        return [r.strip() for r in self.github_repos.split(",") if r.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
