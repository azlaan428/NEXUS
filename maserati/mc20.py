# maserati/mc20.py — Twitter reply drafter

import sqlite3
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("mc20")

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
                "max_tokens": 80,
                "temperature": 0.7
            },
            timeout=20
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"mc20: groq call failed — {e}")
        return ""


def build_prompt(intel: dict) -> str:
    user = intel.get("user_data", intel.get("owner_data", {}))
    owner = intel.get("owner", "")
    name = user.get("name") or owner
    bio = user.get("bio") or ""
    repos = intel.get("top_repos", [])
    top_work = repos[0]["name"] if repos else "their projects"

    return f"""Write a Twitter/X reply that would get a smart technical person's attention. You are Azlaan, a Biomedical Engineering student building AI agents.

Person: {name} (@{user.get('twitter') or owner})
Bio: {bio}
Known for: {top_work}

Rules:
- Under 240 characters
- Reply to their most likely recent post topic based on their bio/work
- Genuine, adds value or asks something smart — not a pitch
- No hashtags, no emojis unless natural
- Sounds like a real person, not marketing

Return only the reply text."""


def draft_replies():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    profiles = c.execute("""
        SELECT id, raw_intel FROM profiles
        WHERE raw_intel LIKE '%"twitter"%'
        AND raw_intel NOT LIKE '%"twitter": ""%'
        AND raw_intel NOT LIKE '%"twitter": null%'
        AND id NOT IN (
            SELECT p2.id FROM profiles p2
            JOIN outreach o ON o.channel = 'twitter_reply'
            WHERE o.target_id = p2.id OR o.queue_id IS NULL
        )
        LIMIT 10
    """).fetchall()

    if not profiles:
        log.info("mc20: no profiles with Twitter handles")
        conn.close()
        return

    drafted = 0
    for row in profiles:
        try:
            intel = json.loads(row["raw_intel"])
        except Exception:
            continue

        user = intel.get("user_data", intel.get("owner_data", {}))
        twitter = user.get("twitter", "")
        if not twitter:
            continue

        draft = ask_groq(build_prompt(intel))
        if not draft:
            continue

        c.execute("""
            INSERT INTO outreach (target_id, queue_id, channel, draft, tone, sent, drafted_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (None, None, "twitter_reply", draft, "conversational", 0))

        drafted += 1
        log.info(f"mc20: drafted reply for @{twitter}")

    conn.commit()
    conn.close()
    log.info(f"mc20: done — {drafted} replies drafted")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    draft_replies()
