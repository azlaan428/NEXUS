# bugatti/veyron.py — queue retrieval helper

import sqlite3
import os
import logging
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("veyron")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_pending(limit: int = 20) -> list:
    """Queue entries not yet reviewed."""
    conn = _connect()
    rows = conn.execute("""
        SELECT q.*, s.url, s.raw_content, s.relevance_score
        FROM queue q
        LEFT JOIN signals s ON q.signal_id = s.id
        WHERE q.reviewed = 0
        ORDER BY q.priority DESC, q.queued_at ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_approved(limit: int = 20) -> list:
    """Queue entries approved by human or LLM."""
    conn = _connect()
    rows = conn.execute("""
        SELECT q.*, s.url, s.raw_content, s.relevance_score
        FROM queue q
        LEFT JOIN signals s ON q.signal_id = s.id
        WHERE q.reviewed = 1 OR q.approved = 1
        ORDER BY q.priority DESC, q.queued_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_priority(min_priority: int = 2) -> list:
    """Queue entries at or above a given priority level."""
    conn = _connect()
    rows = conn.execute("""
        SELECT q.*, s.url, s.raw_content, s.relevance_score
        FROM queue q
        LEFT JOIN signals s ON q.signal_id = s.id
        WHERE q.priority >= ?
        ORDER BY q.priority DESC, q.queued_at DESC
    """, (min_priority,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pending = get_pending(5)
    log.info(f"veyron: {len(pending)} pending queue entries")
