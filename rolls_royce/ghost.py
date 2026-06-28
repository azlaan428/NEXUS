# rolls_royce/ghost.py — judge panel routes (targets and profiles)

import sqlite3
import os
import json
import logging
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("ghost")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

ghost = Blueprint("ghost", __name__)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@ghost.route("/api/judges")
def list_judges():
    conn = _connect()
    rows = conn.execute("""
        SELECT id, name, title, company, linkedin, twitter, github, source, added_at
        FROM targets
        ORDER BY added_at DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@ghost.route("/api/judges", methods=["POST"])
def add_judge():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = _connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO targets (name, title, company, linkedin, twitter, github, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        data.get("title", ""),
        data.get("company", ""),
        data.get("linkedin", ""),
        data.get("twitter", ""),
        data.get("github", ""),
        data.get("source", "manual")
    ))
    conn.commit()
    new_id = c.lastrowid
    conn.close()

    log.info(f"ghost: added target {name} (id {new_id})")
    return jsonify({"status": "created", "id": new_id}), 201


@ghost.route("/api/judges/<int:target_id>/profile")
def judge_profile(target_id):
    conn = _connect()
    c = conn.cursor()

    target = c.execute("""
        SELECT id, name, title, company, linkedin, twitter, github
        FROM targets WHERE id = ?
    """, (target_id,)).fetchone()

    if not target:
        conn.close()
        return jsonify({"error": "not found"}), 404

    profiles = c.execute("""
        SELECT id, raw_intel, summary, angle, built_at, last_refreshed
        FROM profiles
        WHERE target_id = ?
        ORDER BY built_at DESC
        LIMIT 1
    """, (target_id,)).fetchone()

    conn.close()

    result = dict(target)
    if profiles:
        p = dict(profiles)
        try:
            p["raw_intel"] = json.loads(p["raw_intel"])
        except Exception:
            pass
        result["profile"] = p
    else:
        result["profile"] = None

    return jsonify(result)
