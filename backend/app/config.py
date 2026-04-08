"""Configuration management with DB-backed settings."""

import os
import time
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


# DB settings cache
_settings_cache = {}
_cache_timestamp = 0
_CACHE_TTL = 60  # seconds


def _load_settings_from_db():
    """Load all settings from the database. Returns empty dict on failure."""
    global _settings_cache, _cache_timestamp
    now = time.time()
    if _settings_cache and (now - _cache_timestamp) < _CACHE_TTL:
        return _settings_cache

    try:
        from .db import execute_query
        rows = execute_query("SELECT key, value FROM settings")
        _settings_cache = {row["key"]: row["value"] for row in (rows or [])}
        _cache_timestamp = now
    except Exception:
        pass

    return _settings_cache


def invalidate_settings_cache():
    """Force next get() call to re-read from DB."""
    global _settings_cache, _cache_timestamp
    _settings_cache = {}
    _cache_timestamp = 0


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'foresight-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    JSON_AS_ASCII = False

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # Neo4j
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE', 'foresight')
    GRAPH_MEMORY_ENABLED = os.environ.get('GRAPH_MEMORY_ENABLED', 'false').lower() == 'true'

    # Embeddings
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'voyage-3-lite')
    EMBEDDING_API_KEY = os.environ.get('EMBEDDING_API_KEY')

    # Reddit (still needed for PRAW direct usage)
    REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'Foresight/1.0')

    @classmethod
    def get(cls, key: str) -> str:
        """Get a config value from DB settings only. No .env fallback for API keys."""
        settings = _load_settings_from_db()
        return settings.get(key, "")

    @classmethod
    def validate(cls):
        errors = []
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL not configured in .env")
        return errors

    @classmethod
    def is_llm_configured(cls) -> bool:
        """Check if an LLM provider is ready to use."""
        return bool(cls.get("llm_api_key"))
