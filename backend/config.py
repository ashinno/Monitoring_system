import os

class Settings:
    PROJECT_NAME: str = "Sentinel Monitoring System"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    # Default to SQLite for local dev if not specified
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkeywhichshouldbechangedinprod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Celery / Redis
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

settings = Settings()
