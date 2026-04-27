import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR.parent / "ressources" / "ai_summaries.json"
DB_FILE    = BASE_DIR.parent / "ressources" / "cyber.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            url                 TEXT UNIQUE,
            title               TEXT,
            ai_title_fr         TEXT,
            source_name         TEXT,
            source_label        TEXT,
            category            TEXT,
            section             TEXT,
            published           TEXT,
            score               INTEGER,
            ai_summary          TEXT,
            ai_priority         TEXT,
            ai_why_it_matters   TEXT,
            inserted_at         TEXT
        )
    """)
    conn.commit()


def insert_articles(conn: sqlite3.Connection, articles: list[dict]) -> tuple[int, int]:
    inserted = 0
    skipped  = 0
    now      = datetime.now(timezone.utc).isoformat()

    for article in articles:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO articles
                (url, title, ai_title_fr, source_name, source_label,
                 category, section, published, score,
                 ai_summary, ai_priority, ai_why_it_matters, inserted_at)
            VALUES
                (:url, :title, :ai_title_fr, :source_name, :source_label,
                 :category, :section, :published, :score,
                 :ai_summary, :ai_priority, :ai_why_it_matters, :inserted_at)
        """, {**article, "inserted_at": now})

        if cursor.rowcount == 1:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    return inserted, skipped


def main() -> None:
    articles = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    print(f"{len(articles)} articles lus depuis {INPUT_FILE.name}")

    with get_connection() as conn:
        create_table(conn)
        inserted, skipped = insert_articles(conn, articles)

    print(f"Insérés : {inserted} | Ignorés (doublons) : {skipped}")


if __name__ == "__main__":
    main()
