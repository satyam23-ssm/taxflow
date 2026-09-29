import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # Core
    SECRET_KEY: str = "taxflow-fastapi-dev-secret-key-change-in-production"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL") or (
        "sqlite+aiosqlite:////tmp/taxflow.db" if os.getenv("VERCEL") else "sqlite+aiosqlite:///./taxflow.db"
    )

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # JWT
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # AI / OCR
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OCR_ENGINE: str = "gemini"
    OPENAI_API_KEY: str = ""

    # WhatsApp
    WHATSAPP_GRAPH_API_VERSION: str = "v23.0"
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""

    # GSP
    GSP_PROVIDER_NAME: str = ""
    GSP_BASE_URL: str = ""
    GSP_API_KEY: str = ""
    GSP_CLIENT_ID: str = ""
    GSP_CLIENT_SECRET: str = ""

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        case_sensitive = False
        extra = "ignore"


settings = Settings()
