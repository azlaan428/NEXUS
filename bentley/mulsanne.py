# bentley/mulsanne.py — relevance ranker, scores based on bentayga intel

import sqlite3
import os
import json
import logging

log = logging.getLogger("mulsanne")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

TOPIC_KEYWORDS = ["ai", "llm", "agent", "agentic", "automation", "ml", "gpt", "langchain", "groq", "amd", "inference", "transformer", "rag", "embeddings"]
BIO_KEYWORDS = ["ai", "ml", "researcher", "engineer", "founder", "open source", "llm", "deep learning"]


def score_profile(intel: dict) -> float:
    repo = intel.get("repo_data", {})
    owner = intel.get("owner_data", {})
    score = 0.0

    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)
    issues = repo.get("open_issues", 0)

    if stars > 10000: score += 3.0
    elif stars > 1000: score += 1.5
    elif stars > 100: score += 0.5

    if forks > 1000: score += 2.0
    elif forks > 100: score += 1.0

    if issues > 50: score += 0.5

    topics = repo.get("topics", [])
    for topic in topics:
        if any(kw in topic.lower() for kw in TOPIC_KEYWORDS):
            score += 1.0

    desc = repo.get("description", "").lower()
    for kw in TOPIC_KEYWORDS:
        if kw in desc:
            score += 0.5

    followers = owner.get("followers", 0)
    if followers > 10000: score += 3.0
    elif followers > 1000: score += 1.5
    elif followers > 100: score += 0.5

    bio = (owner.get("bio") or "").lower()
    for kw in BIO_KEYWORDS:
        if kw in bio:
            score += 0.5

    return round(score, 2)


def rank_pending():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    profiles = c.execute("""
        SELECT id as profile_id, raw_intel
        FROM profiles
        ORDER BY built_at DESC
        LIMIT 50
    """).fetchall()

    queued = c.execute("""
        SELECT id as queue_id, signal_id
        FROM queue
        WHERE recommended_action = 'bentley_score'
        AND reviewed = 0
    """).fetchall()

    if not profiles or not queued:
        log.info("mulsanne: nothing to rank")
        conn.close()
        return

    rows = []
    for p, q in zip(profiles, queued):
        rows.append({
            "profile_id": p["profile_id"],
            "raw_intel": p["raw_intel"],
            "queue_id": q["queue_id"],
            "signal_id": q["signal_id"]
        })

    log.info(f"mulsanne: ranking {len(rows)} profiles")

    for row in rows:
        try:
            intel = json.loads(row["raw_intel"])
        except Exception:
            continue

        score = score_profile(intel)
        owner = intel.get("owner", "unknown")
        repo = intel.get("repo", "unknown")

        if score >= 10:
            priority = 3
            action = "high_priority_review"
        elif score >= 5:
            priority = 2
            action = "bentley_score"
        else:
            priority = 1
            action = "low_priority"

        c.execute("""
            UPDATE queue
            SET priority = ?, recommended_action = ?, reasoning = ?
            WHERE id = ?
        """, (
            priority,
            action,
            f"Mulsanne score {score} — stars/forks/owner influence weighted",
            row["queue_id"]
        ))

        log.info(f"mulsanne: {owner}/{repo} → score {score}, priority {priority}")

    conn.commit()
    conn.close()
    log.info("mulsanne: done")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    rank_pending()