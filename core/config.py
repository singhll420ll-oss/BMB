"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Bite Me Buddy"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/bitemebuddy"
    DATABASE_SYNC_URL: str = "postgresql://postgres:password@localhost:5432/bitemebuddy"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_EMAIL: str = "admin@bitemebuddy.com"
    ADMIN_PHONE: str = "+919876543210"
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    UPLOAD_DIR: str = "static/uploads"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Create upload directories
UPLOAD_DIRS = {
    "services": os.path.join(settings.UPLOAD_DIR, "services"),
    "menu": os.path.join(settings.UPLOAD_DIR, "menu"),
    "plans": os.path.join(settings.UPLOAD_DIR, "plans"),
    "users": os.path.join(settings.UPLOAD_DIR, "users")
}
