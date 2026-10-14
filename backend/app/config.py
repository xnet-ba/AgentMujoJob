"""Centralna konfiguracija — sve tajne isključivo iz environmenta, nikad API ključevi AI provajdera."""
import os


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


class Settings:
    APP_NAME: str = "AgentMujoJob"
    APP_ENV: str = _get("APP_ENV", "dev")
    BACKEND_HOST: str = _get("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(_get("BACKEND_PORT", "8010") or 8010)
    # Admin (obavezno za /admin/*)
    ADMIN_TOKEN: str = _get("ADMIN_TOKEN", "")
    # AI jezgro: isključivo OpenCode CLI s besplatnim modelima — NEMA API ključeva ni fallback provajdera.
    # Prijava se radi jednom na serveru: `opencode auth login`. Model: `opencode models`.
    OPENCODE_BIN: str = _get("OPENCODE_BIN", "opencode")
    OPENCODE_MODEL: str = _get("OPENCODE_MODEL", "")  # prazno = podrazumijevani model CLI-ja
    OPENCODE_TIMEOUT: int = int(_get("OPENCODE_TIMEOUT", "45") or 45)
    # CORS
    CORS_ORIGINS: str = _get("CORS_ORIGINS", "http://localhost:3000")
    # Rate limit
    RATE_LIMIT_PER_MIN: int = int(_get("RATE_LIMIT_PER_MIN", "60") or 60)
    AI_RATE_LIMIT_PER_MIN: int = int(_get("AI_RATE_LIMIT_PER_MIN", "10") or 10)


settings = Settings()
