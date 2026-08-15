import os
from datetime import timedelta
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'quickdrop.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    MAX_FILES_PER_SHARE = int(os.getenv("MAX_FILES_PER_SHARE", "5"))
    MAX_TEXT_SIZE_MB = int(os.getenv("MAX_TEXT_SIZE_MB", "1"))
    DEFAULT_EXPIRATION_SECONDS = int(os.getenv("DEFAULT_EXPIRATION_SECONDS", "3600"))
    MAX_EXPIRATION_SECONDS = int(os.getenv("MAX_EXPIRATION_SECONDS", "86400"))
    RATELIMIT_DEFAULT = os.getenv("RATE_LIMIT", "200 per day, 50 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "data" / "uploads")))
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "quickdrop")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
