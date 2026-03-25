# Version: v0.1.0 | Date: 2026-03-24
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "evony_enemy_analytics")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

BRONZE_RAW_DIR = BASE_DIR / "data" / "bronze" / "raw"
BRONZE_PARSED_DIR = BASE_DIR / "data" / "bronze" / "parsed"
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"

for path in [BRONZE_RAW_DIR, BRONZE_PARSED_DIR, SILVER_DIR, GOLD_DIR]:
    path.mkdir(parents=True, exist_ok=True)

def sqlalchemy_url() -> str:
    return f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


