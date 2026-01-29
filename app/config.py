"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    """
    Application settings from environment variables
    """
    
    # ============ API SETTINGS ============
    API_TITLE: str = Field(
        default="Kurumsal Bütçe Sistemi API",
        description="API başlığı"
    )
    API_DESCRIPTION: str = Field(
        default="Kurumsal bütçe planlama, yönetimi ve analizi sistemi",
        description="API açıklaması"
    )
    API_VERSION: str = Field(
        default="1.0.0",
        description="API versiyonu"
    )
    
    # ============ DATABASE SETTINGS ============
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://budgetuser:budgetpass123@localhost:5432/budget_system",
        description="PostgreSQL connection string"
    )
    
    # ============ REDIS SETTINGS ============
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    # ============ CORS SETTINGS ============
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
    # ============ JWT SETTINGS ============
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production-with-a-strong-random-key-min-32-chars-12345",
        description="JWT secret key - Production'da değiştir!"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_HOURS: int = Field(
        default=24,
        description="Token geçerlilik süresi (saat)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()