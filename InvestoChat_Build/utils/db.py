"""Database utilities"""

import os
import psycopg
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL")


def _pg() -> psycopg.Connection:
    """Get PostgreSQL connection"""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DATABASE_URL)


def _table_exists(cur, name: str) -> bool:
    """Check if a table exists in the database"""
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        )
    """, (name,))
    return cur.fetchone()[0]


def _doc_tuple_to_meta(row) -> dict:
    """Convert database row tuple to metadata dict"""
    source_path, page, tags, project_id, doc_type = row[1:6]
    return {
        "source": source_path,
        "page": page,
        "tags": tags,
        "project_id": project_id,
        "type": doc_type
    }
