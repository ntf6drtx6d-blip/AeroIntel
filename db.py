import sqlite3
import datetime

conn = sqlite3.connect("aerointel_sources.db", check_same_thread=False)
cursor = conn.cursor()


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discovered_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT,
        seed_name TEXT,
        seed_type TEXT,
        page_title TEXT,
        page_url TEXT UNIQUE,
        page_domain TEXT,
        relevance_score INTEGER,
        reason TEXT,
        status TEXT,
        discovered_at TEXT
    )
    """)
    conn.commit()


def page_exists(page_url):
    cursor.execute("SELECT 1 FROM discovered_pages WHERE page_url = ?", (page_url,))
    return cursor.fetchone() is not None


def save_page(record):
    cursor.execute(
        """
        INSERT OR IGNORE INTO discovered_pages (
            country, seed_name, seed_type, page_title, page_url,
            page_domain, relevance_score, reason, status, discovered_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("country"),
            record.get("seed_name"),
            record.get("seed_type"),
            record.get("page_title"),
            record.get("page_url"),
            record.get("page_domain"),
            record.get("relevance_score"),
            record.get("reason"),
            record.get("status", "new"),
            str(datetime.datetime.now()),
        ),
    )
    conn.commit()


def update_page_status(page_url, status):
    cursor.execute(
        "UPDATE discovered_pages SET status = ? WHERE page_url = ?",
        (status, page_url),
    )
    conn.commit()


def get_pages(country=None):
    if country:
        cursor.execute("""
            SELECT country, seed_name, seed_type, page_title, page_url,
                   page_domain, relevance_score, reason, status, discovered_at
            FROM discovered_pages
            WHERE country = ?
            ORDER BY relevance_score DESC, discovered_at DESC
        """, (country,))
    else:
        cursor.execute("""
            SELECT country, seed_name, seed_type, page_title, page_url,
                   page_domain, relevance_score, reason, status, discovered_at
            FROM discovered_pages
            ORDER BY relevance_score DESC, discovered_at DESC
        """)
    return cursor.fetchall()


def clear_pages():
    cursor.execute("DELETE FROM discovered_pages")
    conn.commit()
