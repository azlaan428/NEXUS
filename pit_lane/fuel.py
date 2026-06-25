# pit_lane/fuel.py — database initializer, runs once on ignition

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "podium.db")


def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT,
            company TEXT,
            linkedin TEXT,
            twitter TEXT,
            github TEXT,
            source TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            raw_content TEXT,
            url TEXT,
            relevance_score REAL DEFAULT 0.0,
            processed INTEGER DEFAULT 0,
            caught_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER REFERENCES signals(id),
            target_id INTEGER REFERENCES targets(id),
            recommended_action TEXT,
            reasoning TEXT,
            priority INTEGER DEFAULT 0,
            reviewed INTEGER DEFAULT 0,
            approved INTEGER DEFAULT 0,
            queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER REFERENCES targets(id),
            raw_intel TEXT,
            summary TEXT,
            angle TEXT,
            built_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER REFERENCES targets(id),
            queue_id INTEGER REFERENCES queue(id),
            channel TEXT,
            draft TEXT,
            tone TEXT,
            sent INTEGER DEFAULT 0,
            drafted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("pit_lane: podium.db initialized")


if __name__ == "__main__":
    init()