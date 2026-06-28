# rolls_royce/cullinan.py — queue review routes (approve / skip / pending)

import sqlite3
import os
import logging
from flask import Blueprint, jsonify
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("cullinan")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

cullinan = Blueprint("cullinan", __name__)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@cullinan.route("/api/queue/<int:queue_id>/approve", methods=["POST"])
def approve(queue_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        UPDATE queue SET approved = 1, reviewed = 1 WHERE id = ?
    """, (queue_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()

    if not affected:
        return jsonify({"error": "not found"}), 404

    log.info(f"cullinan: approved queue id {queue_id}")
    return jsonify({"status": "approved", "id": queue_id})


@cullinan.route("/api/queue/<int:queue_id>/skip", methods=["POST"])
def skip(queue_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        UPDATE queue SET reviewed = 1, approved = 0 WHERE id = ?
    """, (queue_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()

    if not affected:
        return jsonify({"error": "not found"}), 404

    log.info(f"cullinan: skipped queue id {queue_id}")
    return jsonify({"status": "skipped", "id": queue_id})


@cullinan.route("/api/queue/pending")
def pending():
    conn = _connect()
    rows = conn.execute("""
        SELECT q.id, q.signal_id, q.recommended_action, q.reasoning,
               q.priority, q.reviewed, q.approved, q.queued_at,
               s.url, s.raw_content, s.relevance_score
        FROM queue q
        LEFT JOIN signals s ON q.signal_id = s.id
        WHERE q.reviewed = 0
        ORDER BY q.priority DESC, q.queued_at ASC
        LIMIT 50
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
