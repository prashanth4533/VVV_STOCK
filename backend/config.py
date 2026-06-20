import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-key")

    # MySQL connection - single source of truth, no SQLite fallback.
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_DATABASE_URI")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "vvv_stock")
    DB_USER = os.getenv("DB_USER", "vvv_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    _DB_USER = quote_plus(DB_USER)
    _DB_PASSWORD = quote_plus(DB_PASSWORD)
    _DB_NAME = quote_plus(DB_NAME)

    _COMPONENT_DATABASE_URI = (
        f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{_DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or _COMPONENT_DATABASE_URI
    _DB_URL = make_url(SQLALCHEMY_DATABASE_URI)
    if _DB_URL.get_backend_name() != "mysql":
        raise RuntimeError(
            "Only MySQL database URLs are supported. Set DATABASE_URL to mysql+pymysql://..."
        )
    # Managed providers often emit a bare `mysql://` scheme, which SQLAlchemy
    # maps to the MySQLdb driver. Only PyMySQL is installed, so force it.
    if _DB_URL.get_driver_name() in ("", "mysqldb"):
        _DB_URL = _DB_URL.set(drivername="mysql+pymysql")
    SQLALCHEMY_DATABASE_URI = _DB_URL.render_as_string(hide_password=False)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "pool_timeout": 30,
    }

    # CORS — allow local dev ports and production
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
