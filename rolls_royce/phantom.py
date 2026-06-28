# rolls_royce/phantom.py — main Flask blueprint: dashboard and API routes

import sqlite3
import os
import json
import logging
from flask import Blueprint, jsonify, current_app, send_from_directory
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("phantom")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

phantom = Blueprint("phantom", __name__)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _profile_for_owner(c, owner: str) -> dict:
    row = c.execute("""
        SELECT raw_intel, summary, angle FROM profiles
        WHERE raw_intel LIKE ?
        LIMIT 1
    """, (f'%"owner": "{owner}"%',)).fetchone()
    if not row:
        return {}
    try:
        intel = json.loads(row["raw_intel"])
    except Exception:
        intel = {}
    return {
        "summary": row["summary"],
        "angle": row["angle"],
        "photo_url": intel.get("photo_url", ""),
        "followers": (intel.get("user_data") or intel.get("owner_data") or {}).get("followers", 0)
    }


@phantom.route("/")
def index():
    return send_from_directory(current_app.static_folder, "index.html")


@phantom.route("/api/queue")
def api_queue():
    conn = _connect()
    c = conn.cursor()

    rows = c.execute("""
        SELECT q.id, q.signal_id, q.recommended_action, q.reasoning,
               q.priority, q.reviewed, q.approved, q.queued_at,
               s.url, s.raw_content, s.relevance_score, s.source
        FROM queue q
        LEFT JOIN signals s ON q.signal_id = s.id
        ORDER BY q.priority DESC, q.queued_at DESC
        LIMIT 20
    """).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        owner = ""
        if row["url"]:
            parts = row["url"].rstrip("/").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
        item["profile"] = _profile_for_owner(c, owner) if owner else {}
        items.append(item)

    conn.close()
    return jsonify(items)


@phantom.route("/api/signals")
def api_signals():
    conn = _connect()
    rows = conn.execute("""
        SELECT id, source, raw_content, url, relevance_score, processed, caught_at
        FROM signals
        ORDER BY caught_at DESC
        LIMIT 50
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@phantom.route("/api/stats")
def api_stats():
    conn = _connect()
    c = conn.cursor()

    total_signals = c.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    total_queue = c.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
    pending_review = c.execute("SELECT COUNT(*) FROM queue WHERE reviewed = 0").fetchone()[0]
    approved = c.execute("SELECT COUNT(*) FROM queue WHERE reviewed = 1 OR approved = 1").fetchone()[0]
    total_outreach = c.execute("SELECT COUNT(*) FROM outreach").fetchone()[0]
    sent_outreach = c.execute("SELECT COUNT(*) FROM outreach WHERE sent = 1").fetchone()[0]

    conn.close()
    return jsonify({
        "total_signals": total_signals,
        "total_queue": total_queue,
        "pending_review": pending_review,
        "approved": approved,
        "total_outreach": total_outreach,
        "sent_outreach": sent_outreach
    })
