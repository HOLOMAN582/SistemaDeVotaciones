from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    database_url: str = "sqlite:///./votaciones.db"
    jwt_secret_key: str = "change-this-development-secret"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
