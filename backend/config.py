import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""

    # Database Configuration
    # For Amvera PostgreSQL:
    # postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://reyting_user:password@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
    )

    # API
    api_title: str = "Dashboard API"
    api_version: str = "1.0.0"
    api_description: str = "API для интерактивного дашборда оценки эффективности глав МО"

    # CORS - Add production domains
    cors_origins: list = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "https://aleksey341.github.io",
        "https://aleksey341.github.io/Reyting",
    ]

    # File uploads
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Data processing
    batch_size: int = 1000

    # Environment
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"

    class Config:
        case_sensitive = False


settings = Settings()
