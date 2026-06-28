# jaguar/f_type.py — image resolver, fetches GitHub avatar URLs into profiles

import sqlite3
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("f_type")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")


def resolve_photos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    profiles = c.execute("""
        SELECT id, raw_intel FROM profiles
        WHERE raw_intel IS NOT NULL
        LIMIT 50
    """).fetchall()

    if not profiles:
        log.info("f_type: no profiles found")
        conn.close()
        return

    updated = 0
    for row in profiles:
        try:
            intel = json.loads(row["raw_intel"])
        except Exception:
            continue

        if intel.get("photo_url"):
            continue

        owner = intel.get("owner")
        if not owner:
            continue

        photo_url = f"https://github.com/{owner}.png"
        try:
            r = requests.head(photo_url, timeout=5, allow_redirects=True)
            if r.status_code != 200:
                continue
        except Exception:
            continue

        intel["photo_url"] = photo_url
        c.execute(
            "UPDATE profiles SET raw_intel = ? WHERE id = ?",
            (json.dumps(intel), row["id"])
        )
        updated += 1
        log.info(f"f_type: {owner} → {photo_url}")

    conn.commit()
    conn.close()
    log.info(f"f_type: done — {updated} photos resolved")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resolve_photos()
