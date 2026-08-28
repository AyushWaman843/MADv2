import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _normalize_database_url(database_url: str) -> str:
    # Supabase sometimes provides postgres:// URLs, while SQLAlchemy expects postgresql://.
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
    MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "")
    MSG91_VIRTUAL_NUMBER = os.getenv("MSG91_VIRTUAL_NUMBER", "")
    DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///voicecaller.db"))
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
