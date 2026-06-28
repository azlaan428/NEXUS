# jaguar/xj220.py — deep angle synthesis via Groq

import sqlite3
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("xj220")

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
                "max_tokens": 150,
                "temperature": 0.5
            },
            timeout=20
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"xj220: groq call failed — {e}")
        return ""


def build_prompt(intel: dict) -> str:
    user = intel.get("user_data", intel.get("owner_data", {}))
    repos = intel.get("top_repos", [])
    repo_line = "; ".join(
        f"{r['name']} ({r.get('stars', 0)} stars)" for r in repos[:3]
    ) if repos else "no public repos"

    owner = intel.get("owner", "unknown")
    return f"""You are NEXUS, an outreach intelligence system. Write a single sentence describing the best way to open a conversation with this GitHub user for an AI/agent collaboration.

Name: {user.get('name') or owner}
Bio: {user.get('bio') or 'none'}
Company: {user.get('company') or 'none'}
Blog/Links: {user.get('blog') or 'none'}
Twitter: {user.get('twitter') or 'none'}
Followers: {user.get('followers', 0)}
Top repos: {repo_line}

Return only one sentence. Be specific to what they actually build — no generic openers."""


def synthesize_angles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    profiles = c.execute("""
        SELECT id, raw_intel FROM profiles
        WHERE (angle IS NULL OR angle = '')
        AND raw_intel IS NOT NULL
        LIMIT 20
    """).fetchall()

    if not profiles:
        log.info("xj220: no profiles need angles")
        conn.close()
        return

    log.info(f"xj220: synthesizing angles for {len(profiles)} profiles")

    for row in profiles:
        try:
            intel = json.loads(row["raw_intel"])
        except Exception:
            continue

        angle = ask_groq(build_prompt(intel))
        if not angle:
            continue

        c.execute("UPDATE profiles SET angle = ? WHERE id = ?", (angle, row["id"]))
        log.info(f"xj220: {intel.get('owner', '?')} → {angle[:80]}...")

    conn.commit()
    conn.close()
    log.info("xj220: done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    synthesize_angles()
