# ferrari/sf90.py — GitHub trending watcher, always running hot

import requests
import logging
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")
log = logging.getLogger("sf90")

GITHUB_TRENDING_URL = "https://github.com/trending"
GITHUB_API_URL = "https://api.github.com/search/repositories"


def fetch_trending(language: str = "", since: str = "daily") -> list:
    """
    Fetch trending repos from GitHub.
    
    language: filter by language e.g. "python", "" for all
    since: "daily", "weekly", "monthly"
    
    Returns list of dicts with repo data.
    """
    try:
        params = {
            "q": f"stars:>100{f' language:{language}' if language else ''}",
            "sort": "stars",
            "order": "desc",
            "per_page": 25
        }

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "NEXUS-SF90-Watcher"
        }

        response = requests.get(GITHUB_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        repos = data.get("items", [])

        results = []
        for repo in repos:
            results.append({
                "name": repo.get("full_name"),
                "description": repo.get("description", ""),
                "url": repo.get("html_url"),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", ""),
                "topics": repo.get("topics", []),
                "created_at": repo.get("created_at", ""),
                "updated_at": repo.get("updated_at", ""),
                "fetched_at": datetime.utcnow().isoformat()
            })

        log.info(f"SF90: fetched {len(results)} trending repos (lang={language or 'all'}, since={since})")
        return results

    except requests.exceptions.RequestException as e:
        log.error(f"SF90: fetch failed — {e}")
        return []

def save_signals(repos: list):
    """Write fetched repos into podium.db signals table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for repo in repos:
        c.execute("""
            INSERT INTO signals (source, raw_content, url, relevance_score)
            VALUES (?, ?, ?, ?)
        """, (
            "sf90_github",
            f"{repo['name']} — {repo['description']}",
            repo['url'],
            repo['stars'] / 1000.0  # rough relevance proxy for now
        ))
    conn.commit()
    conn.close()
    log.info(f"SF90: {len(repos)} signals written to podium")

def watch(language: str = "python") -> list:
    log.info(f"SF90: ignition — watching GitHub trending ({language})")
    results = fetch_trending(language=language)
    if results:
        save_signals(results)
    return results

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    results = watch("python")
    print(json.dumps(results[:3], indent=2))