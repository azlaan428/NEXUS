# maserati/gransport.py — cold email drafter

import sqlite3
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("gransport")

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
                "max_tokens": 250,
                "temperature": 0.6
            },
            timeout=20
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"gransport: groq call failed — {e}")
        return ""


def build_prompt(intel: dict, angle: str) -> str:
    user = intel.get("user_data", intel.get("owner_data", {}))
    owner = intel.get("owner", "there")
    name = user.get("name") or owner
    bio = user.get("bio") or ""
    company = user.get("company") or ""
    repos = intel.get("top_repos", [])
    repo_list = ", ".join(r["name"] for r in repos[:3]) if repos else ""

    return f"""Write a cold email that doesn't read like a cold email. You are Azlaan, a Biomedical Engineering student and AI/agent builder.

Target: {name}
Bio: {bio}
Company: {company}
Notable work: {repo_list}
Angle: {angle}

Rules:
- Under 150 words total
- Reference something specific from their actual work
- One ask only — not a pitch, just a genuine connection attempt
- No "hope this finds you well" or other filler
- Sign off as Azlaan

Return only the email body. No subject line."""


def draft_emails():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    queue_rows = c.execute("""
        SELECT q.id as queue_id, q.signal_id, s.url
        FROM queue q
        JOIN signals s ON q.signal_id = s.id
        WHERE q.reviewed = 1
        AND q.id NOT IN (
            SELECT DISTINCT queue_id FROM outreach WHERE queue_id IS NOT NULL
        )
        LIMIT 10
    """).fetchall()

    if not queue_rows:
        log.info("gransport: nothing to draft")
        conn.close()
        return

    log.info(f"gransport: {len(queue_rows)} approved entries to draft")

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
            log.info(f"gransport: no profile for {owner}, skipping")
            continue

        try:
            intel = json.loads(profile["raw_intel"])
        except Exception:
            continue

        angle = profile["angle"] or "direct and specific about their open source work"
        draft = ask_groq(build_prompt(intel, angle))

        if not draft:
            continue

        c.execute("""
            INSERT INTO outreach (target_id, queue_id, channel, draft, tone, sent, drafted_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (None, row["queue_id"], "email", draft, "direct", 0))

        log.info(f"gransport: drafted email for {owner}")

    conn.commit()
    conn.close()
    log.info("gransport: done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    draft_emails()
