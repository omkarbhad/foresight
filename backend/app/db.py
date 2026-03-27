"""Supabase PostgreSQL connection pool"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from .config import Config
from .utils.logger import get_logger

logger = get_logger('foresight.db')

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=Config.DATABASE_URL
        )
        logger.info("Database connection pool created")
    return _pool


@contextmanager
def get_connection():
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


@contextmanager
def get_cursor():
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()


def execute_query(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params)
        try:
            return cur.fetchall()
        except psycopg2.ProgrammingError:
            return None


def execute_one(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params)
        try:
            return cur.fetchone()
        except psycopg2.ProgrammingError:
            return None


def execute_write(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.rowcount
