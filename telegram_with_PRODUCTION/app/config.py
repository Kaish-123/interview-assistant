"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TechyEra Marketing"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True
    APP_URL: str = "http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/techyera_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_BUSINESS: str = ""
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Subscription Plans Configuration
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "max_telegram_accounts": 1,
        "max_groups": 5,
        "max_messages_per_day": 10,
        "auto_growth": False,
        "analytics": False,
        "priority_support": False,
    },
    "starter": {
        "name": "Starter",
        "price": 19,
        "max_telegram_accounts": 1,
        "max_groups": 50,
        "max_messages_per_day": 100,
        "auto_growth": True,
        "analytics": True,
        "priority_support": False,
    },
    "pro": {
        "name": "Pro",
        "price": 49,
        "max_telegram_accounts": 3,
        "max_groups": 200,
        "max_messages_per_day": 500,
        "auto_growth": True,
        "analytics": True,
        "priority_support": True,
    },
    "business": {
        "name": "Business",
        "price": 99,
        "max_telegram_accounts": 10,
        "max_groups": -1,  # Unlimited
        "max_messages_per_day": -1,  # Unlimited
        "auto_growth": True,
        "analytics": True,
        "priority_support": True,
    },
}


settings = Settings()

