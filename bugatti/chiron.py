# bugatti/chiron.py — queue storage helper

import sqlite3
import os
import logging
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("chiron")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")


def add_to_queue(signal_id: int, action: str, reasoning: str, priority: int) -> int:
    """Insert a signal into the queue. Returns the new row id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO queue (signal_id, recommended_action, reasoning, priority, reviewed, approved)
        VALUES (?, ?, ?, ?, 0, 0)
    """, (signal_id, action, reasoning, priority))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    log.debug(f"chiron: queued signal {signal_id} as {action} (priority {priority}) → queue id {row_id}")
    return row_id


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("chiron: queue storage helper — no standalone action")
