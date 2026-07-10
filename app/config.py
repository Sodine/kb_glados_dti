import os
from datetime import timedelta


def _bool_env(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "sim", "on"}


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "troque-esta-chave-em-producao")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_SCHEMA = os.getenv("SUPABASE_SCHEMA", "bot_atendimento_ti")
    KB_TABLE = os.getenv("KB_TABLE", "base_conhecimento")
    USERS_TABLE = os.getenv("USERS_TABLE", "usuarios_painel")
    SUPABASE_TIMEOUT = int(os.getenv("SUPABASE_TIMEOUT", "20"))

    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    BOOTSTRAP_ADMIN = _bool_env("BOOTSTRAP_ADMIN", True)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.getenv("SESSION_LIFETIME_HOURS", "12"))
    )
