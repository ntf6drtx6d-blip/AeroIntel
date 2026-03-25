import sqlite3
import datetime

conn = sqlite3.connect("aerointel_sources.db", check_same_thread=False)
cursor = conn.cursor()


def column_exists(table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    return any(col[1] == column_name for col in cols)


def ensure_column(table_name: str, column_name: str, column_type: str, default_sql: str = ""):
    if not column_exists(table_name, column_name):
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_sql:
            sql += f" DEFAULT {default_sql}"
        cursor.execute(sql)
        conn.commit()


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
        page_category TEXT,
        status TEXT,
        discovered_at TEXT,
        body_text TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discovered_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT,
        source_url TEXT,
        entity_name TEXT,
        entity_type TEXT,
        rationale TEXT,
        discovered_at TEXT
    )
    """)
    conn.commit()

    ensure_column("discovered_pages", "page_category", "TEXT", "'other'")
    ensure_column("discovered_pages", "status", "TEXT", "'new'")
    ensure_column("discovered_pages", "discovered_at", "TEXT")
    ensure_column("discovered_pages", "reason", "TEXT")
    ensure_column("discovered_pages", "relevance_score", "INTEGER", "0")
    ensure_column("discovered_pages", "page_domain", "TEXT")
    ensure_column("discovered_pages", "seed_name", "TEXT")
    ensure_column("discovered_pages", "seed_type", "TEXT")
    ensure_column("discovered_pages", "body_text", "TEXT")

    ensure_column("discovered_entities", "country", "TEXT")
    ensure_column("discovered_entities", "source_url", "TEXT")
    ensure_column("discovered_entities", "entity_name", "TEXT")
    ensure_column("discovered_entities", "entity_type", "TEXT")
    ensure_column("discovered_entities", "rationale", "TEXT")
    ensure_column("discovered_entities", "discovered_at", "TEXT")


def page_exists(page_url):
    cursor.execute("SELECT 1 FROM discovered_pages WHERE page_url = ?", (page_url,))
    return cursor.fetchone() is not None


def save_page(record):
    cursor.execute(
        """
        INSERT OR IGNORE INTO discovered_pages (
            country, seed_name, seed_type, page_title, page_url,
            page_domain, relevance_score, reason, page_category, status, discovered_at, body_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            record.get("page_category", "other"),
            record.get("status", "new"),
            str(datetime.datetime.now()),
            record.get("body_text"),
        ),
    )
    conn.commit()


def save_entity(record):
    cursor.execute(
        """
        INSERT INTO discovered_entities (
            country, source_url, entity_name, entity_type, rationale, discovered_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("country"),
            record.get("source_url"),
            record.get("entity_name"),
            record.get("entity_type"),
            record.get("rationale"),
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
                   page_domain, relevance_score, reason, page_category, status, discovered_at, body_text
            FROM discovered_pages
            WHERE country = ?
            ORDER BY relevance_score DESC, discovered_at DESC
        """, (country,))
    else:
        cursor.execute("""
            SELECT country, seed_name, seed_type, page_title, page_url,
                   page_domain, relevance_score, reason, page_category, status, discovered_at, body_text
            FROM discovered_pages
            ORDER BY relevance_score DESC, discovered_at DESC
        """)
    return cursor.fetchall()


def get_entities(country=None):
    if country:
        cursor.execute("""
            SELECT country, source_url, entity_name, entity_type, rationale, discovered_at
            FROM discovered_entities
            WHERE country = ?
            ORDER BY discovered_at DESC
        """, (country,))
    else:
        cursor.execute("""
            SELECT country, source_url, entity_name, entity_type, rationale, discovered_at
            FROM discovered_entities
            ORDER BY discovered_at DESC
        """)
    return cursor.fetchall()


def clear_pages():
    cursor.execute("DELETE FROM discovered_pages")
    cursor.execute("DELETE FROM discovered_entities")
    conn.commit()
