from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis & Celery (worker backend)
    REDIS_URL: str
    CELERY_CONCURRENCY: int = 4

    # Storage (MinIO / S3)
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "aadhaar-platform"

    # Security
    UIDAI_PUBLIC_KEY_PATH: str = "certs/uidai_auth.pem"
    ENCRYPTION_KEY: str          # 32-byte hex for Fernet
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API Settings
    API_PREFIX: str = "/api/v1"
    APP_VERSION: str = "1.0.0"
    RATE_LIMIT_PER_MINUTE: int = 100
    MAX_BULK_UPLOAD_MB: int = 500
    MAX_BULK_FILES: int = 500
    WEBHOOK_RETRY_COUNT: int = 3

    # Features
    LIVENESS_ENABLED: bool = False

    # Logging / Monitoring
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
