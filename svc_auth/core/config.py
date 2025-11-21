from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из .env файла"""

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
