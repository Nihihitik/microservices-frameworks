from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Настройки приложения из .env файла"""

    # Database
    DATABASE_URL: Optional[str] = None
    DB_USER: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("DB_USER", "PROJECTS_DB_USER")
    )
    DB_PASSWORD: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("DB_PASSWORD", "PROJECTS_DB_PASSWORD")
    )
    DB_HOST: str = Field(
        default="localhost", validation_alias=AliasChoices("DB_HOST", "PROJECTS_DB_HOST")
    )
    DB_PORT: int = Field(
        default=5432, validation_alias=AliasChoices("DB_PORT", "PROJECTS_DB_PORT")
    )
    DB_NAME: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("DB_NAME", "PROJECTS_DB_NAME")
    )

    # JWT (для валидации токенов от svc_auth)
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8002

    # External Services
    AUTH_SERVICE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Возвращает безопасный SQLAlchemy URL, учитывая спецсимволы в пароле."""
        url = self._build_database_url_from_components()
        if url:
            return url
        if self.DATABASE_URL:
            return self.DATABASE_URL
        raise ValueError(
            "DATABASE_URL или DB_USER/DB_PASSWORD/DB_NAME должны быть заданы"
        )

    def _build_database_url_from_components(self) -> Optional[str]:
        if not all([self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            return None

        sqlalchemy_url = URL.create(
            "postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

        return sqlalchemy_url.render_as_string(hide_password=False)


settings = Settings()
