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
