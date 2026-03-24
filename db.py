import sqlite3
import datetime

conn = sqlite3.connect("aerointel.db", check_same_thread=False)
cursor = conn.cursor()


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discovered_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT,
        query TEXT,
        title TEXT,
        url TEXT,
        domain TEXT,
        source_type TEXT,
        relevance_score INTEGER,
        rationale TEXT,
        discovered_at TEXT
    )
    """)
    conn.commit()


def source_exists(url):
    cursor.execute("SELECT 1 FROM discovered_sources WHERE url = ?", (url,))
    return cursor.fetchone() is not None


def save_source(record):
    cursor.execute(
        """
        INSERT INTO discovered_sources (
            country, query, title, url, domain, source_type,
            relevance_score, rationale, discovered_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("country"),
            record.get("query"),
            record.get("title"),
            record.get("url"),
            record.get("domain"),
            record.get("source_type"),
            record.get("relevance_score"),
            record.get("rationale"),
            str(datetime.datetime.now()),
        ),
    )
    conn.commit()


def get_sources(country=None):
    if country:
        cursor.execute("""
            SELECT country, query, title, url, domain, source_type, relevance_score, rationale, discovered_at
            FROM discovered_sources
            WHERE country = ?
            ORDER BY relevance_score DESC, discovered_at DESC
        """, (country,))
    else:
        cursor.execute("""
            SELECT country, query, title, url, domain, source_type, relevance_score, rationale, discovered_at
            FROM discovered_sources
            ORDER BY relevance_score DESC, discovered_at DESC
        """)
    return cursor.fetchall()


def clear_sources():
    cursor.execute("DELETE FROM discovered_sources")
    conn.commit()
