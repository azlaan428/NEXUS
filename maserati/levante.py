# maserati/levante.py — LinkedIn message drafter (under 300 chars)

import sqlite3
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("levante")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def ask_groq(prompt: str) -> str:
    try:
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.6
            },
            timeout=20
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"levante: groq call failed — {e}")
        return ""


def build_prompt(intel: dict, angle: str) -> str:
    user = intel.get("user_data", intel.get("owner_data", {}))
    owner = intel.get("owner", "")
    name = user.get("name") or owner
    repos = intel.get("top_repos", [])
    top_repo = repos[0]["name"] if repos else "your work"

    return f"""Write a LinkedIn connection message. You are Azlaan, a Biomedical Engineering student and AI/agent builder.

Target: {name}
Their standout project: {top_repo}
Angle: {angle}

Rules:
- Under 300 characters total
- No "I came across your profile" opener
- Reference one specific thing they built
- One clear reason to connect — no pitch
- Do not sign off, LinkedIn already shows your name

Return only the message text."""


def draft_linkedin():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    queue_rows = c.execute("""
        SELECT q.id as queue_id, q.signal_id, s.url
        FROM queue q
        JOIN signals s ON q.signal_id = s.id
        WHERE q.reviewed = 1
        AND q.id NOT IN (
            SELECT DISTINCT queue_id FROM outreach
            WHERE queue_id IS NOT NULL AND channel = 'linkedin'
        )
        LIMIT 10
    """).fetchall()

    if not queue_rows:
        log.info("levante: nothing to draft")
        conn.close()
        return

    log.info(f"levante: {len(queue_rows)} entries to draft LinkedIn messages for")

    for row in queue_rows:
        parts = row["url"].rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner = parts[-2]

        profile = c.execute("""
            SELECT id, raw_intel, angle FROM profiles
            WHERE raw_intel LIKE ?
            LIMIT 1
        """, (f'%"owner": "{owner}"%',)).fetchone()

        if not profile:
            continue

        try:
            intel = json.loads(profile["raw_intel"])
        except Exception:
            continue

        angle = profile["angle"] or "their open source AI work"
        draft = ask_groq(build_prompt(intel, angle))

        if not draft:
            continue

        if len(draft) > 300:
            draft = draft[:297] + "..."

        c.execute("""
            INSERT INTO outreach (target_id, queue_id, channel, draft, tone, sent, drafted_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (None, row["queue_id"], "linkedin", draft, "direct", 0))

        log.info(f"levante: drafted LinkedIn for {owner} ({len(draft)} chars)")

    conn.commit()
    conn.close()
    log.info("levante: done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    draft_linkedin()
