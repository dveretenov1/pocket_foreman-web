# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Pocket Foreman API"
    VERSION: str = "1.0.0"
    FLASK_ENV: Optional[str] = None
    FLASK_APP: Optional[str] = None
    
    # Database Settings
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URL: str | None = None
    
    # AWS Settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_REGION: str = "us-east-1"
    
    # API Keys
    ANTHROPIC_API_KEY: str
    
    # Firebase
    FIREBASE_SERVICE_ACCOUNT_PATH: str
    
    # Stripe Settings
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_BASIC: str
    STRIPE_PRICE_ID_PRO: str
    STRIPE_PRICE_ID_ENTERPRISE: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # Makes env vars case-insensitive

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
