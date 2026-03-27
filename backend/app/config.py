"""Configuration management"""

import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'foresight-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    JSON_AS_ASCII = False

    # Claude
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    CLAUDE_MODEL_NAME = os.environ.get('CLAUDE_MODEL_NAME', 'claude-sonnet-4-20250514')
    # Alias for CrewAI LLM configuration (reads same key)
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLAUDE_API_KEY')

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # News API
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')

    # Reddit
    REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'Foresight/1.0')

    # Twitter
    TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

    # Finnhub
    FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

    # Neo4j
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE', 'foresight')
    GRAPH_MEMORY_ENABLED = os.environ.get('GRAPH_MEMORY_ENABLED', 'false').lower() == 'true'

    # Embeddings
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'voyage-3-lite')
    EMBEDDING_API_KEY = os.environ.get('EMBEDDING_API_KEY')

    @classmethod
    def validate(cls):
        errors = []
        if not cls.CLAUDE_API_KEY:
            errors.append("CLAUDE_API_KEY not configured")
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL not configured")
        return errors
