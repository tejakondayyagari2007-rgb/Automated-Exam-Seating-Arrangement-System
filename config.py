import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def get_secret_key(environment, configured_key):
    production = environment.strip().lower() in {"prod", "production"}
    configured_key = (configured_key or "").strip()
    if configured_key:
        if len(configured_key) < 32 or configured_key == "change_this_secret_key":
            raise RuntimeError("SECRET_KEY must be at least 32 characters and must not use a known default.")
        return configured_key
    if production:
        raise RuntimeError("SECRET_KEY must be configured in production.")
    return secrets.token_urlsafe(32)


class Config:
    ENVIRONMENT = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).strip().lower()
    SECRET_KEY = get_secret_key(ENVIRONMENT, os.getenv("SECRET_KEY"))
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "exam_seating_system")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENVIRONMENT in {"prod", "production"}
    JSON_SORT_KEYS = False


config = Config()
