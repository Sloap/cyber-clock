from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from pathlib import Path

app = FastAPI()
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")

@app.get("/")
def index(request: Request):
    articles = json.loads(Path("ressources/ai_summaries.json").read_text())
    return templates.TemplateResponse(request, "index.html", {
        "articles": articles
    })
