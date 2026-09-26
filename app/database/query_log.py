"""
SQLite-based query logging for audit trail and analytics.

Logs every question asked, the sources retrieved, and the response generated.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class QueryLogger:
    """Lightweight query logging with SQLite."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.query_log_db
        self._init_db()

    def _init_db(self) -> None:
        """Create the query log table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    question TEXT NOT NULL,
                    document_filter TEXT,
                    chunks_retrieved INTEGER DEFAULT 0,
                    sources TEXT,
                    answer TEXT,
                    relevance_scores TEXT,
                    latency_ms REAL
                )
                """
            )
            conn.commit()

    def log_query(
        self,
        question: str,
        document_filter: str | None = None,
        chunks_retrieved: int = 0,
        sources: list[dict] | None = None,
        answer: str = "",
        relevance_scores: list[float] | None = None,
        latency_ms: float = 0.0,
    ) -> int:
        """Log a query and return the log entry ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO query_log
                    (timestamp, question, document_filter, chunks_retrieved,
                     sources, answer, relevance_scores, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    question,
                    document_filter,
                    chunks_retrieved,
                    json.dumps(sources) if sources else None,
                    answer,
                    json.dumps(relevance_scores) if relevance_scores else None,
                    latency_ms,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_queries(self, limit: int = 20) -> list[dict]:
        """Get the most recent logged queries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, timestamp, question, document_filter,
                       chunks_retrieved, answer, latency_ms
                FROM query_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_stats(self) -> dict:
        """Get query log statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM query_log").fetchone()[0]
            avg_latency = conn.execute(
                "SELECT AVG(latency_ms) FROM query_log WHERE latency_ms > 0"
            ).fetchone()[0]

        return {
            "total_queries": total,
            "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0,
        }
