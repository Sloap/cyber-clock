from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from email.utils import parsedate
from datetime import datetime
import sqlite3
from pathlib import Path

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

def get_articles() -> list[dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM articles
        ORDER BY inserted_at DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/")
def index(request: Request):
    articles = get_articles()
    for article in articles:
        article["published_fr"] = format_date_fr(article.get("published", ""))
    return templates.TemplateResponse(request, "index.html", {
        "articles": articles
    })
