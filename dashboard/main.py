from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from email.utils import parsedate
from datetime import datetime
import json
from pathlib import Path

app = FastAPI()
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")

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

@app.get("/")
def index(request: Request):
    articles = json.loads(Path("ressources/ai_summaries.json").read_text())
    for article in articles:
        article["published_fr"] = format_date_fr(article.get("published", ""))
    return templates.TemplateResponse(request, "index.html", {
        "articles": articles
    })
