"""
Application configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "COBOL to Java Migration System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"   # Vite dev server alternative
    ]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cobol_migration"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Storage (S3/MinIO)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "cobol-migration"
    S3_REGION: str = "us-east-1"
    
    # Git
    GITHUB_TOKEN: str = ""
    GITLAB_TOKEN: str = ""
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4.1-mini"
    
    # CrewAI
    CREWAI_VERBOSE: bool = True
    CREWAI_MEMORY: bool = True
    
    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Jobs
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_MINUTES: int = 120
    
    # Paths
    TEMP_DIR: str = "/tmp/cobol-migration"
    REPOS_DIR: str = "/tmp/cobol-migration/repos"
    ARTIFACTS_DIR: str = "/tmp/cobol-migration/artifacts"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
