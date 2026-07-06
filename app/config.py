import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SQLITE_URL = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"


def normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def parse_csv_env(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL))
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-for-production-workout-journal")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
ALGORITHM = "HS256"
API_PREFIX = "/api"
STATIC_DIR = Path(os.getenv("STATIC_DIR", BASE_DIR / "static"))
CORS_ORIGINS = parse_csv_env(
    os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:3000,http://localhost:3000,https://mavravetasyan.github.io",
    )
)
LOGIN_CODE_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
LOGIN_CODE_LENGTH = int(os.getenv("LOGIN_CODE_LENGTH", "6"))
LOGIN_CODE_RESEND_SECONDS = int(os.getenv("LOGIN_CODE_RESEND_SECONDS", "30"))
LOGIN_CODE_MAX_ATTEMPTS = int(os.getenv("LOGIN_CODE_MAX_ATTEMPTS", "5"))
DEBUG_AUTH_CODES = os.getenv("DEBUG_AUTH_CODES", "1") == "1"
MAIL_PROVIDER = os.getenv("MAIL_PROVIDER", "log").strip().lower()
MAIL_FROM = os.getenv("MAIL_FROM", "Workout Journal <no-reply@example.com>")
MAIL_REPLY_TO = os.getenv("MAIL_REPLY_TO", "").strip()
APP_NAME = os.getenv("APP_NAME", "Workout Journal").strip() or "Workout Journal"
APP_LOGIN_URL = os.getenv("APP_LOGIN_URL", "").strip()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
