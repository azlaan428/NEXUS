# bugatti/divo.py — queue prioritizer, re-ranks based on age and score

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("divo")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

STALE_HOURS = 24
LOW_PRIORITY_THRESHOLD = 1


def reprioritize():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    cutoff = (datetime.utcnow() - timedelta(hours=STALE_HOURS)).isoformat()

    stale = c.execute("""
        SELECT id, priority, recommended_action, queued_at
        FROM queue
        WHERE reviewed = 0
        AND queued_at < ?
    """, (cutoff,)).fetchall()

    if not stale:
        log.info("divo: no stale queue entries to re-rank")
        conn.close()
        return

    log.info(f"divo: re-ranking {len(stale)} stale entries")

    bumped = 0
    dropped = 0

    for row in stale:
        if row["priority"] <= LOW_PRIORITY_THRESHOLD:
            # low-priority items older than 24h get marked reviewed=-1 (dropped)
            c.execute("""
                UPDATE queue SET reviewed = -1, reasoning = reasoning || ' | divo: stale drop'
                WHERE id = ?
            """, (row["id"],))
            dropped += 1
            log.info(f"divo: dropped stale low-priority queue id {row['id']}")
        else:
            # higher-priority items get their priority bumped +1 to keep them visible
            new_priority = min(row["priority"] + 1, 5)
            c.execute("""
                UPDATE queue SET priority = ?, reasoning = reasoning || ' | divo: age bump'
                WHERE id = ?
            """, (new_priority, row["id"]))
            bumped += 1
            log.info(f"divo: bumped queue id {row['id']} → priority {new_priority}")

    conn.commit()
    conn.close()
    log.info(f"divo: done — {bumped} bumped, {dropped} dropped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reprioritize()
