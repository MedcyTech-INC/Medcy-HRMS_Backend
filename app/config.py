from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Medcy Health Tech HRMS API"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./medcy_hrms.db"

    # JWT Authentication
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production_medcy_hrms_2026"
    JWT_REFRESH_SECRET: str = "super_secret_refresh_jwt_key_change_in_production_medcy_hrms_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis (Optional)
    REDIS_URL: Optional[str] = None

    # Supabase (Storage & Proxy)
    SUPABASE_URL: str = "https://srv1674496.hstgr.cloud"
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "hrms-photos"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:9580",
        "https://localhost:9580",
        "http://localhost:9590",
        "http://127.0.0.1:9580",
        "https://127.0.0.1:9580",
        "https://srv1674496.hstgr.cloud",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
