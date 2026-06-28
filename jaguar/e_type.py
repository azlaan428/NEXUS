# jaguar/e_type.py — web intel, finds the human behind a high-priority signal

import sqlite3
import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("e_type")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "User-Agent": "NEXUS-EType"
}


def fetch_user(owner: str) -> dict:
    try:
        r = requests.get(f"https://api.github.com/users/{owner}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        d = r.json()
        return {
            "name": d.get("name", ""),
            "bio": d.get("bio", ""),
            "company": d.get("company", ""),
            "blog": d.get("blog", ""),
            "twitter": d.get("twitter_username", ""),
            "location": d.get("location", ""),
            "followers": d.get("followers", 0),
            "public_repos": d.get("public_repos", 0)
        }
    except Exception as e:
        log.error(f"e_type: user fetch failed — {e}")
        return {}


def fetch_top_repos(owner: str) -> list:
    try:
        r = requests.get(
            f"https://api.github.com/users/{owner}/repos",
            headers=HEADERS,
            params={"sort": "stars", "per_page": 5},
            timeout=10
        )
        r.raise_for_status()
        return [
            {
                "name": repo.get("name", ""),
                "description": repo.get("description", ""),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", ""),
                "topics": repo.get("topics", [])
            }
            for repo in r.json()
        ]
    except Exception as e:
        log.error(f"e_type: top repos fetch failed — {e}")
        return []


def profile_pending():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute("""
        SELECT q.id as queue_id, q.signal_id, s.url
        FROM queue q
        JOIN signals s ON q.signal_id = s.id
        WHERE q.recommended_action = 'high_priority_review'
        AND q.reviewed = 0
    """).fetchall()

    if not rows:
        log.info("e_type: no high-priority signals to profile")
        conn.close()
        return

    existing = c.execute("SELECT raw_intel FROM profiles").fetchall()
    known_owners = set()
    for row in existing:
        try:
            known_owners.add(json.loads(row["raw_intel"]).get("owner", ""))
        except Exception:
            pass
    known_owners.discard("")

    log.info(f"e_type: {len(rows)} high-priority entries, {len(known_owners)} already profiled")

    built = 0
    for row in rows:
        parts = row["url"].rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner = parts[-2]

        if owner in known_owners:
            continue

        user_data = fetch_user(owner)
        top_repos = fetch_top_repos(owner)

        intel = {
            "owner": owner,
            "source": "e_type",
            "user_data": user_data,
            "top_repos": top_repos,
            "profiled_at": datetime.utcnow().isoformat()
        }

        name = user_data.get("name") or owner
        bio = user_data.get("bio") or "no bio"

        c.execute("""
            INSERT INTO profiles (target_id, raw_intel, summary, built_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (None, json.dumps(intel), f"{name} — {bio}"))

        known_owners.add(owner)
        built += 1
        log.info(f"e_type: profiled {owner} — {user_data.get('followers', 0)} followers")

    conn.commit()
    conn.close()
    log.info(f"e_type: done — {built} profiles built")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    profile_pending()
