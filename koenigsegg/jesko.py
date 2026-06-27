# koenigsegg/jesko.py — signal router, directs incoming feeds

import sqlite3
import os
import logging
from datetime import datetime

log = logging.getLogger("jesko")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

SCORE_DROP = 11.0
SCORE_BENTLEY = 13.0


def route():
    """
    Pull all processed but unqueued signals and route them based on score.
    < 11      → drop, not worth pursuing
    11 to 13  → send to Bentley for deeper scoring
    > 13      → straight to queue as high priority
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, source, raw_content, url, relevance_score
        FROM signals
        WHERE processed = 1
        AND id NOT IN (SELECT DISTINCT signal_id FROM queue WHERE signal_id IS NOT NULL)
    """).fetchall()

    if not rows:
        log.info("jesko: no signals to route")
        conn.close()
        return

    log.info(f"jesko: routing {len(rows)} signals")

    dropped = 0
    to_bentley = 0
    to_queue = 0

    for row in rows:
        score = row["relevance_score"]

        if score < SCORE_DROP:
            dropped += 1
            log.info(f"jesko: DROP — {row['url']} (score {score})")
            continue

        if score <= SCORE_BENTLEY:
            # send to Bentley — insert into queue with low priority, unreviewed
            c.execute("""
                INSERT INTO queue (signal_id, recommended_action, reasoning, priority, reviewed)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["id"],
                "bentley_score",
                f"Score {score} — needs deeper evaluation",
                1,
                0
            ))
            to_bentley += 1
            log.info(f"jesko: BENTLEY — {row['url']} (score {score})")

        else:
            # high priority, straight to queue
            c.execute("""
                INSERT INTO queue (signal_id, recommended_action, reasoning, priority, reviewed)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["id"],
                "high_priority_review",
                f"Score {score} — high relevance, immediate attention",
                3,
                0
            ))
            to_queue += 1
            log.info(f"jesko: HIGH PRIORITY — {row['url']} (score {score})")

    conn.commit()
    conn.close()
    log.info(f"jesko: done — {dropped} dropped, {to_bentley} to Bentley, {to_queue} high priority")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    route()