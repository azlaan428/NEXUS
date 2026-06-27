# koenigsegg/ccxr.py — deduplication, kills noise

import sqlite3
import os
import logging

log = logging.getLogger("ccxr")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")


def deduplicate():
    """
    Find and remove duplicate signals based on URL.
    Keeps the highest scoring version, deletes the rest.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    dupes = c.execute("""
        SELECT url, COUNT(*) as count
        FROM signals
        GROUP BY url
        HAVING count > 1
    """).fetchall()

    if not dupes:
        log.info("ccxr: no duplicates found")
        conn.close()
        return

    log.info(f"ccxr: found {len(dupes)} duplicate URLs")

    removed = 0
    for url, count in dupes:
        # get all rows for this url, ordered by score desc
        rows = c.execute("""
            SELECT id FROM signals
            WHERE url = ?
            ORDER BY relevance_score DESC, caught_at ASC
        """, (url,)).fetchall()

        # keep the first (highest score), delete the rest
        ids_to_delete = [row[0] for row in rows[1:]]
        c.execute(f"""
            DELETE FROM signals
            WHERE id IN ({','.join('?' * len(ids_to_delete))})
        """, ids_to_delete)

        removed += len(ids_to_delete)
        log.info(f"ccxr: {url} — kept 1, removed {len(ids_to_delete)}")

    conn.commit()
    conn.close()
    log.info(f"ccxr: done — {removed} duplicates removed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    deduplicate()