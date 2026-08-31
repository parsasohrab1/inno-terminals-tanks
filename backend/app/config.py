"""Central configuration (12-factor, env driven)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"),
        env_prefix="INNO_",
        extra="ignore",
    )

    # --- app ---
    app_name: str = "INNO Terminals & Tanks"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # --- database ---
    # dev default: local SQLite; prod: set INNO_DATABASE_URL to a TimescaleDB/Postgres DSN
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'inno.sqlite3').as_posix()}"

    # --- auth / security (NFR-3.1, NFR-3.2) ---
    secret_key: str = "dev-only-change-me-in-production-please-32b"
    access_token_expire_minutes: int = 60 * 8
    algorithm: str = "HS256"
    mfa_issuer: str = "INNO-Terminals"
    require_mfa: bool = False  # enforce TOTP for privileged roles when True

    # --- proprietary IP vault (patentable modules, appendix 5.3) ---
    # Passphrase for decrypting backend/app/secure/modules/*.py.enc at runtime.
    # If unset, the platform runs with OPEN baseline algorithms only.
    ip_key: str | None = None

    # --- realtime / ingest (FR-1.1, NFR-1.2) ---
    max_ingest_batch: int = 5000
    ws_heartbeat_seconds: int = 20

    # --- alarm engine (FR-4, ISA-18.2) ---
    alarm_rate_limit_per_operator_hour: int = 6
    alarm_flood_window_seconds: int = 60
    alarm_flood_threshold: int = 10

    # --- leak prediction (FR-2) ---
    leak_horizon_minutes: int = 30
    leak_recall_target: float = 0.95
    model_store_dir: Path = BACKEND_DIR / "models_store"

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.model_store_dir.mkdir(parents=True, exist_ok=True)
    return s


settings = get_settings()
