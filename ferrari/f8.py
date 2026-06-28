# ferrari/f8.py — Reddit watcher, pulls from r/MachineLearning

import sqlite3
import os
import json
import logging
import requests
from datetime import datetime

log = logging.getLogger("f8")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

SUBREDDITS = ["MachineLearning", "LocalLLaMA", "artificial"]
REDDIT_URL = "https://www.reddit.com/r/{sub}/new.json?limit=25"

HEADERS = {"User-Agent": "NEXUS-F8/1.0"}

KEYWORDS = ["github", "agent", "llm", "model", "inference", "open source", "paper", "release"]


def score_post(post: dict) -> float:
    score = 0.0
    text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
    for kw in KEYWORDS:
        if kw in text:
            score += 1.0
    ups = post.get("ups", 0)
    if ups > 1000:
        score += 3.0
    elif ups > 100:
        score += 1.5
    elif ups > 10:
        score += 0.5
    return round(score, 2)


def fetch_subreddit(sub: str) -> list:
    try:
        r = requests.get(REDDIT_URL.format(sub=sub), headers=HEADERS, timeout=10)
        r.raise_for_status()
        posts = r.json().get("data", {}).get("children", [])
        return [p["data"] for p in posts if p.get("data")]
    except Exception as e:
        log.error(f"f8: fetch failed for r/{sub} — {e}")
        return []


def watch():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    existing_urls = set(
        row[0] for row in c.execute("SELECT url FROM signals WHERE source LIKE 'f8_%'").fetchall()
    )

    written = 0
    for sub in SUBREDDITS:
        posts = fetch_subreddit(sub)
        for post in posts:
            url = post.get("url") or f"https://reddit.com{post.get('permalink', '')}"
            if url in existing_urls:
                continue

            relevance = score_post(post)
            if relevance < 1.0:
                continue

            raw = json.dumps({
                "title": post.get("title", ""),
                "subreddit": sub,
                "ups": post.get("ups", 0),
                "permalink": post.get("permalink", ""),
                "fetched_at": datetime.utcnow().isoformat()
            })

            c.execute("""
                INSERT INTO signals (source, raw_content, url, relevance_score)
                VALUES (?, ?, ?, ?)
            """, (f"f8_{sub}", raw, url, relevance))

            existing_urls.add(url)
            written += 1

    conn.commit()
    conn.close()
    log.info(f"f8: done — {written} new signals from Reddit")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watch()
