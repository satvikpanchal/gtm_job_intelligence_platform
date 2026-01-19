"""Database connection utilities."""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import DB_CONFIG


def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def get_cursor(dict_cursor=True):
    """Context manager for database cursor."""
    conn = get_connection()
    cursor_factory = RealDictCursor if dict_cursor else None
    try:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def init_database():
    """Initialize database schema."""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    with open(schema_path) as f:
        schema_sql = f.read()
    
    with get_cursor() as cursor:
        cursor.execute(schema_sql)
    
    print("✅ Database schema initialized")


if __name__ == "__main__":
    init_database()
