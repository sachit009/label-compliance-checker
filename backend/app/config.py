"""
Label Compliance Checker — Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OCR Engine: "paddle", "gcloud_vision", or "mock"
    OCR_ENGINE: Literal["paddle", "gcloud_vision", "mock"] = "paddle"

    # Database (SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./label_compliance.db"

    # Google Cloud Vision (only needed if OCR_ENGINE == "gcloud_vision")
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Upload limits
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    # Upload directory
    UPLOAD_DIR: str = "./uploads"

    # NLP
    SPACY_MODEL: str = "en_core_web_sm"
    CONFIDENCE_THRESHOLD: float = 0.5  # Below this, field is marked ILLEGIBLE

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Label Compliance Checker"
    VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
