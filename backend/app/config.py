"""Centralna konfiguracija — sve tajne isključivo iz environmenta."""
import os


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


class Settings:
    APP_NAME: str = "AgentMujoJob"
    APP_ENV: str = _get("APP_ENV", "dev")
    BACKEND_HOST: str = _get("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(_get("BACKEND_PORT", "8010") or 8010)
    DATA_DIR: str = _get("DATA_DIR", "/home/sha/AgentMujoJob/backend/data")
    # Appwrite (opcionalno — bez ključa radi lokalni JSON store)
    APPWRITE_ENDPOINT: str = _get("APPWRITE_ENDPOINT", "https://baza.kolektiv.pro/v1")
    APPWRITE_PROJECT_ID: str = _get("APPWRITE_PROJECT_ID", "")
    APPWRITE_API_KEY: str = _get("APPWRITE_API_KEY", "")
    APPWRITE_DB_ID: str = _get("APPWRITE_DB_ID", "")
    # Admin (obavezno za /admin/*)
    ADMIN_TOKEN: str = _get("ADMIN_TOKEN", "")
    # AI (sve opcionalno — fallback radi bez ključeva)
    AI_PROVIDER: str = _get("AI_PROVIDER", "auto")  # auto|fallback|ollama|openai|anthropic|openrouter
    OPENAI_API_KEY: str = _get("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = _get("ANTHROPIC_API_KEY", "")
    OPENROUTER_API_KEY: str = _get("OPENROUTER_API_KEY", "")
    OLLAMA_URL: str = _get("OLLAMA_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = _get("OLLAMA_MODEL", "qwen3:1.7b")
    # CORS
    CORS_ORIGINS: str = _get("CORS_ORIGINS", "http://localhost:3000")
    # Rate limit
    RATE_LIMIT_PER_MIN: int = int(_get("RATE_LIMIT_PER_MIN", "60") or 60)
    AI_RATE_LIMIT_PER_MIN: int = int(_get("AI_RATE_LIMIT_PER_MIN", "10") or 10)


settings = Settings()
