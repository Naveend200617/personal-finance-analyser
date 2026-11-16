import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    # MySQL via PyMySQL (default). Falls back to SQLite for demo/testing if not set.
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # SQLite fallback so the project runs instantly without MySQL installed.
        # Switch to MySQL by setting DATABASE_URL in .env (see .env.example).
        SQLALCHEMY_DATABASE_URI = "sqlite:///pocketwise.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24  # 1 day
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
