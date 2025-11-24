from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings from .env file"""

    # JWT (for token validation from svc_auth)
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8004

    # External Services
    DEFECTS_SERVICE_URL: str
    PROJECTS_SERVICE_URL: str
    AUTH_SERVICE_URL: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), case_sensitive=True, extra="ignore"
    )


settings = Settings()
