# ferrari/laferrari.py — ArXiv watcher, pulls recent cs.AI and cs.LG papers

import sqlite3
import os
import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

log = logging.getLogger("laferrari")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pit_lane", "podium.db")

ARXIV_URL = (
    "http://export.arxiv.org/api/query"
    "?search_query=cat:cs.AI+OR+cat:cs.LG"
    "&sortBy=submittedDate&sortOrder=descending&max_results=15"
)

NS = {"atom": "http://www.w3.org/2005/Atom"}

KEYWORDS = ["agent", "llm", "language model", "inference", "rag", "tool", "autonomous", "reasoning"]


def score_paper(title: str, summary: str) -> float:
    text = (title + " " + summary).lower()
    score = 0.0
    for kw in KEYWORDS:
        if kw in text:
            score += 1.5
    return round(score, 2)


def fetch_papers() -> list:
    try:
        r = requests.get(ARXIV_URL, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        papers = []
        for entry in root.findall("atom:entry", NS):
            title = (entry.findtext("atom:title", "", NS) or "").strip()
            summary = (entry.findtext("atom:summary", "", NS) or "").strip()
            link_el = entry.find("atom:id", NS)
            url = link_el.text.strip() if link_el is not None and link_el.text else ""
            authors = [
                a.findtext("atom:name", "", NS)
                for a in entry.findall("atom:author", NS)
            ]
            papers.append({
                "title": title,
                "summary": summary[:300],
                "url": url,
                "authors": authors[:5],
                "fetched_at": datetime.utcnow().isoformat()
            })
        return papers
    except Exception as e:
        log.error(f"laferrari: fetch failed — {e}")
        return []


def watch():
    papers = fetch_papers()
    if not papers:
        log.info("laferrari: no papers fetched")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    existing_urls = set(
        row[0] for row in c.execute("SELECT url FROM signals WHERE source = 'laferrari_arxiv'").fetchall()
    )

    written = 0
    for paper in papers:
        if paper["url"] in existing_urls:
            continue

        relevance = score_paper(paper["title"], paper["summary"])
        if relevance < 1.0:
            continue

        c.execute("""
            INSERT INTO signals (source, raw_content, url, relevance_score)
            VALUES (?, ?, ?, ?)
        """, (
            "laferrari_arxiv",
            json.dumps({"title": paper["title"], "summary": paper["summary"], "authors": paper["authors"]}),
            paper["url"],
            relevance
        ))
        existing_urls.add(paper["url"])
        written += 1

    conn.commit()
    conn.close()
    log.info(f"laferrari: done — {written} new ArXiv signals")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watch()
