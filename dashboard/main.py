from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from email.utils import parsedate
from datetime import datetime
import sqlite3
from pathlib import Path
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")

DB_FILE = Path(__file__).resolve().parent.parent / "ressources" / "cyber.db"
MOIS_FR = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"]

def format_date_fr(date_str: str) -> str:
    parsed = parsedate(date_str)
    if parsed:
        dt = datetime(*parsed[:6])
    else:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return date_str
    return f"{dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"

def get_articles(days: Optional[int]) -> list[dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    if days:
        rows = conn.execute("""
            SELECT * FROM articles
            WHERE inserted_at >= datetime('now', ? || ' days')
            ORDER BY inserted_at DESC
        """, (f"-{days}",)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM articles
            ORDER BY inserted_at DESC
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]

def get_stats(days: Optional[int]) -> dict:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    date_filter = "WHERE inserted_at >= datetime('now', :days || ' days')" if days else ""
    params = {"days": f"-{days}"} if days else {}

    counts = conn.execute(f"""
        SELECT ai_priority, COUNT(*) as count
        FROM articles {date_filter}
        GROUP BY ai_priority
    """, params).fetchall()

    total_sources = conn.execute(f"""
        SELECT COUNT(DISTINCT source_name) as count
        FROM articles {date_filter}
    """, params).fetchone()["count"]

    conn.close()

    stats = {"high": 0, "medium": 0, "low": 0, "sources": total_sources}
    for row in counts:
        stats[row["ai_priority"]] = row["count"]
    stats["total"] = stats["high"] + stats["medium"] + stats["low"]

    return stats

@app.get("/")
def index(request: Request, days: Optional[int] = None):
    articles = get_articles(days)
    for article in articles:
        article["published_fr"] = format_date_fr(article.get("published", ""))
    stats = get_stats(days)
    return templates.TemplateResponse(request, "index.html", {
        "articles": articles,
        "stats": stats,
        "days": days,
    })
