import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: Optional[str] = ""
    TELEGRAM_GROUP_ID: Optional[str] = ""
    TELEGRAM_PROXY: Optional[str] = ""
    META_VERIFY_TOKEN: str = "lead_verify_secret_token_2026"
    META_PAGE_ACCESS_TOKEN: Optional[str] = ""
    DATABASE_URL: str = "sqlite:///./crm_leads.db"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ADMIN_PASSWORD: str = "admin123"
    TELEGRAM_CHANNEL_URL: Optional[str] = "https://t.me"
    
    # Eskiz.uz SMS sozlamalari (ixtiyoriy)
    ESKIZ_EMAIL: Optional[str] = ""
    ESKIZ_PASSWORD: Optional[str] = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

