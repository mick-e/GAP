from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    github_token: str
    github_org: str = "bhapi-inc"
    github_repos: str = ""  # Comma-separated list, empty = all repos

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    @property
    def repo_list(self) -> list[str]:
        if not self.github_repos:
            return []
        return [r.strip() for r in self.github_repos.split(",") if r.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
