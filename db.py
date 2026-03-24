import sqlite3
import datetime

conn = sqlite3.connect("signals.db", check_same_thread=False)
cursor = conn.cursor()


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        airport TEXT,
        signal TEXT,
        type TEXT,
        date TEXT,
        source TEXT,
        stage TEXT,
        confidence INTEGER
    )
    """)
    conn.commit()


def signal_exists(signal):
    cursor.execute("SELECT 1 FROM signals WHERE signal = ?", (signal,))
    return cursor.fetchone() is not None


def save_signal(data, source):
    cursor.execute(
        """
        INSERT INTO signals (airport, signal, type, date, source, stage, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("airport"),
            data.get("signal"),
            data.get("type"),
            str(datetime.datetime.now()),
            source,
            data.get("stage"),
            data.get("confidence"),
        ),
    )
    conn.commit()


def get_all_signals():
    cursor.execute("SELECT airport, signal, source, type, stage FROM signals")
    return cursor.fetchall()


def cleanup_old(days=14):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    cursor.execute("DELETE FROM signals WHERE date < ?", (str(cutoff),))
    conn.commit()
