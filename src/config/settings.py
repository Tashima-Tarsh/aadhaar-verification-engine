from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis & Celery
    REDIS_URL: str
    CELERY_CONCURRENCY: int = 4
    
    # Storage
    STORAGE_ENDPOINT: str
    STORAGE_ACCESS_KEY: str
    STORAGE_SECRET_KEY: str
    STORAGE_BUCKET: str = "aadhaar-platform"
    
    # Security
    UIDAI_PUBLIC_KEY_PATH: str
    ENCRYPTION_KEY: str  # 32-byte hex key for Fernet
    JWT_SECRET: str
    
    # API Settings
    RATE_LIMIT_PER_MINUTE: int = 100
    MAX_BULK_UPLOAD_MB: int = 500
    WEBHOOK_RETRY_COUNT: int = 3
    
    # Features
    LIVENESS_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
