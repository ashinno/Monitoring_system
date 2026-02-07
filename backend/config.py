import os
import secrets
from typing import List


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_origins(raw_origins: str) -> List[str]:
    if not raw_origins:
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

class Settings:
    PROJECT_NAME: str = "Sentinel Monitoring System"
    PROJECT_VERSION: str = "1.0.0"
    SENTINEL_ENV: str = os.getenv("SENTINEL_ENV", "development")
    SENTINEL_TESTING: bool = _as_bool(os.getenv("SENTINEL_TESTING"), False)
    
    # Database
    # Default to SQLite for local dev if not specified
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    CORS_ALLOWED_ORIGINS: List[str] = _parse_origins(os.getenv("CORS_ALLOWED_ORIGINS", ""))
    ENFORCE_STRICT_SECURITY: bool = _as_bool(os.getenv("ENFORCE_STRICT_SECURITY"), False)
    DEFAULT_ADMIN_ID: str = os.getenv("DEFAULT_ADMIN_ID", "admin")
    DEFAULT_ADMIN_NAME: str = os.getenv("DEFAULT_ADMIN_NAME", "Admin User")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
    DEFAULT_ANALYST_ID: str = os.getenv("DEFAULT_ANALYST_ID", "analyst")
    DEFAULT_ANALYST_NAME: str = os.getenv("DEFAULT_ANALYST_NAME", "Alice Williams")
    DEFAULT_ANALYST_PASSWORD: str = os.getenv("DEFAULT_ANALYST_PASSWORD", "password")
    
    # Celery / Redis
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

settings = Settings()


def validate_security_posture() -> None:
    insecure_secret = os.getenv("SECRET_KEY") is None
    is_production = settings.SENTINEL_ENV.lower() == "production"

    if insecure_secret and is_production:
        raise RuntimeError(
            "SECRET_KEY must be set explicitly in production. "
            "Refusing to start with an ephemeral signing key."
        )

    if insecure_secret and not settings.SENTINEL_TESTING:
        print(
            "[SECURITY] SECRET_KEY not provided. Using ephemeral key for this process. "
            "Set SECRET_KEY for persistent secure sessions."
        )

    weak_defaults = {
        "admin",
        "password",
        "password123",
        "changeme",
        "123456",
    }
    admin_password = settings.DEFAULT_ADMIN_PASSWORD.strip().lower()
    analyst_password = settings.DEFAULT_ANALYST_PASSWORD.strip().lower()
    using_weak_default_passwords = admin_password in weak_defaults or analyst_password in weak_defaults

    if settings.ENFORCE_STRICT_SECURITY and using_weak_default_passwords:
        raise RuntimeError(
            "Strict security mode requires strong default seeded passwords. "
            "Set DEFAULT_ADMIN_PASSWORD and DEFAULT_ANALYST_PASSWORD to strong values."
        )

    if not settings.SENTINEL_TESTING and using_weak_default_passwords:
        print(
            "[SECURITY] Weak default seeded credentials detected. "
            "Set DEFAULT_ADMIN_PASSWORD and DEFAULT_ANALYST_PASSWORD for secure deployments."
        )


validate_security_posture()
