from pydantic_settings import BaseSettings
from typing import Optional
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "UrgutPlease"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # DB URL
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: str
    SMTP_HOST: str
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # SMS
    ESKIZ_EMAIL: str
    ESKIZ_PASSWORD: str
    
    # Default Admin
    DEFAULT_ADMIN_EMAIL: str = "admin@urgutplease.uz"
    DEFAULT_ADMIN_PASSWORD: str = "Admin123!"
    DEFAULT_ADMIN_FIRSTNAME: str = "Admin"
    DEFAULT_ADMIN_LASTNAME: str = "User"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
