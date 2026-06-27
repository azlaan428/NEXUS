# bentley/continental_gt.py — opportunity scorer, LLM final verdict via Groq

import sqlite3
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("continental_gt")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def ask_groq(prompt: str) -> str:
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.4
            },
            timeout=20
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"continental_gt: groq call failed — {e}")
        return ""


def build_prompt(intel: dict) -> str:
    repo = intel.get("repo_data", {})
    owner = intel.get("owner_data", {})

    return f"""You are NEXUS, an autonomous outreach intelligence system targeting AI/ML builders and researchers for hackathon collaboration and professional networking.

Evaluate this GitHub repository and its owner:

Repo: {intel.get('owner')}/{intel.get('repo')}
Description: {repo.get('description', 'N/A')}
Stars: {repo.get('stars', 0)}
Forks: {repo.get('forks', 0)}
Topics: {', '.join(repo.get('topics', []))}
Language: {repo.get('language', 'N/A')}

Owner followers: {owner.get('followers', 0)}
Owner bio: {owner.get('bio', 'N/A')}
Owner company: {owner.get('company', 'N/A')}

Return a JSON object with exactly these fields:
{{
  "worth_pursuing": true or false,
  "reason": "one sentence why or why not",
  "angle": "one sentence on how to approach this person if worth pursuing",
  "priority": "high", "medium", or "low"
}}

Return only the JSON. No explanation, no markdown.
"""


def evaluate_pending():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    profiles = c.execute("""
        SELECT id, raw_intel FROM profiles
        ORDER BY built_at DESC LIMIT 10
    """).fetchall()

    queued = c.execute("""
        SELECT id as queue_id, signal_id FROM queue
        WHERE recommended_action = 'high_priority_review'
        AND reviewed = 0
    """).fetchall()

    rows = []
    for p, q in zip(profiles, queued):
        rows.append({
            "queue_id": q["queue_id"],
            "signal_id": q["signal_id"],
            "raw_intel": p["raw_intel"]
        })

    if not rows:
        log.info("continental_gt: nothing to evaluate")
        conn.close()
        return

    log.info(f"continental_gt: evaluating {len(rows)} entries")

    for row in rows:
        try:
            intel = json.loads(row["raw_intel"])
        except Exception:
            continue

        prompt = build_prompt(intel)
        verdict_raw = ask_groq(prompt)

        if not verdict_raw:
            continue

        try:
            verdict = json.loads(verdict_raw)
        except Exception:
            log.error(f"continental_gt: could not parse verdict JSON — {verdict_raw}")
            continue

        worth = verdict.get("worth_pursuing", False)
        reason = verdict.get("reason", "")
        angle = verdict.get("angle", "")
        priority_label = verdict.get("priority", "low")

        priority_map = {"high": 3, "medium": 2, "low": 1}
        priority = priority_map.get(priority_label, 1)

        c.execute("""
            UPDATE queue
            SET reasoning = ?, priority = ?, reviewed = ?
            WHERE id = ?
        """, (
            f"{reason} | Angle: {angle}",
            priority,
            1 if worth else -1,
            row["queue_id"]
        ))

        owner = intel.get("owner", "unknown")
        repo = intel.get("repo", "unknown")
        log.info(f"continental_gt: {owner}/{repo} — worth={worth}, priority={priority_label}")
        log.info(f"  reason: {reason}")
        log.info(f"  angle:  {angle}")

    conn.commit()
    conn.close()
    log.info("continental_gt: done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    evaluate_pending()