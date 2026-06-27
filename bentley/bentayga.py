# bentley/bentayga.py — signal to score converter, pulls repo and owner data from GitHub

import os
import requests
import sqlite3
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("bentayga")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "User-Agent": "NEXUS-Bentayga"
}


def fetch_repo_data(owner: str, repo: str) -> dict:
    """Pull full repo metadata from GitHub API."""
    try:
        r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "watchers": data.get("watchers_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "topics": data.get("topics", []),
            "language": data.get("language", ""),
            "description": data.get("description", ""),
            "pushed_at": data.get("pushed_at", "")
        }
    except Exception as e:
        log.error(f"bentayga: repo fetch failed — {e}")
        return {}


def fetch_owner_data(owner: str) -> dict:
    """Pull owner stats from GitHub API."""
    try:
        r = requests.get(f"https://api.github.com/users/{owner}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "followers": data.get("followers", 0),
            "public_repos": data.get("public_repos", 0),
            "company": data.get("company", ""),
            "bio": data.get("bio", ""),
            "twitter": data.get("twitter_username", ""),
            "blog": data.get("blog", "")
        }
    except Exception as e:
        log.error(f"bentayga: owner fetch failed — {e}")
        return {}


def enrich_pending():
    """
    Pull queue entries marked for bentley_score, fetch their GitHub data,
    store enriched intel back into the signals table.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute("""
        SELECT q.id as queue_id, q.signal_id, s.url, s.raw_content
        FROM queue q
        JOIN signals s ON q.signal_id = s.id
        WHERE q.recommended_action = 'bentley_score'
        AND q.reviewed = 0
    """).fetchall()

    if not rows:
        log.info("bentayga: nothing to enrich")
        conn.close()
        return

    log.info(f"bentayga: enriching {len(rows)} signals")

    for row in rows:
        # parse owner/repo from url
        parts = row["url"].rstrip("/").split("/")
        if len(parts) < 2:
            continue

        owner = parts[-2]
        repo = parts[-1]

        repo_data = fetch_repo_data(owner, repo)
        owner_data = fetch_owner_data(owner)

        intel = {
            "owner": owner,
            "repo": repo,
            "repo_data": repo_data,
            "owner_data": owner_data,
            "enriched_at": datetime.utcnow().isoformat()
        }

        import json
        c.execute("""
            INSERT INTO profiles (target_id, raw_intel, summary, built_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            None,
            json.dumps(intel),
            f"{owner}/{repo} — {repo_data.get('description', '')}",
        ))

        log.info(f"bentayga: enriched {owner}/{repo} — {owner_data.get('followers', 0)} followers, {repo_data.get('stars', 0)} stars")

    conn.commit()
    conn.close()
    log.info("bentayga: done")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    enrich_pending()