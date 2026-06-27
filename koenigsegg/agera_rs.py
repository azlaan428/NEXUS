# koenigsegg/agera_rs.py — feed parser, cleans raw signal into structured data

import sqlite3
import os
import logging
from datetime import datetime

log = logging.getLogger("agera_rs")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")


def parse_repo_signal(raw_content: str, url: str) -> dict:
    """
    Parse a raw GitHub repo signal into clean structured data.
    raw_content format: "owner/repo_name — description"
    """
    try:
        name_part, *desc_parts = raw_content.split(" — ", 1)
        description = desc_parts[0].strip() if desc_parts else ""

        if "/" in name_part:
            owner, title = name_part.strip().split("/", 1)
        else:
            owner = ""
            title = name_part.strip()

        return {
            "title": title,
            "owner": owner,
            "summary": description[:500] if description else "",
            "signal_type": "repo",
            "processed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        log.error(f"agera_rs: parse failed — {e}")
        return {}


def score_signal(parsed: dict, raw_score: float) -> float:
    """
    Better relevance scoring than stars/1000.
    Weights: base score + topic bonuses + description quality
    """
    score = min(raw_score, 10.0)  # cap raw score at 10

    summary = parsed.get("summary", "").lower()
    keywords = ["ai", "llm", "agent", "agentic", "automation", "ml", "gpt", "langchain", "groq", "amd"]
    for kw in keywords:
        if kw in summary:
            score += 1.5

    if len(summary) > 50:
        score += 0.5

    return round(min(score, 20.0), 2)


def process_pending():
    """
    Pull all unprocessed signals from podium.db, parse and score them,
    write results back.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, source, raw_content, url, relevance_score
        FROM signals
        WHERE processed = 0
    """).fetchall()

    if not rows:
        log.info("agera_rs: no pending signals")
        conn.close()
        return

    log.info(f"agera_rs: processing {len(rows)} signals")

    for row in rows:
        parsed = parse_repo_signal(row["raw_content"], row["url"])
        if not parsed:
            continue

        new_score = score_signal(parsed, row["relevance_score"])

        c.execute("""
            UPDATE signals
            SET
                processed = 1,
                relevance_score = ?
            WHERE id = ?
        """, (new_score, row["id"]))

        log.info(f"agera_rs: {parsed['owner']}/{parsed['title']} → score {new_score}")

    conn.commit()
    conn.close()
    log.info("agera_rs: done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_pending()