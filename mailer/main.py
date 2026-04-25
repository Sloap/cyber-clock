import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR.parent / "ressources" / "ai_summaries.json"


def load_articles(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_email_body(articles: list[dict]) -> str:
    sections = {
        "Nouvelles vulnérabilités": [],
        "Articles importants": [],
    }

    for article in articles:
        section = article.get("section", "Articles importants")
        sections.setdefault(section, []).append(article)

    lines = []

    lines.append("Bonjour,")
    lines.append("")
    lines.append("Voici ta veille cyber du jour :")
    lines.append("")

    for section_name, section_articles in sections.items():
        if not section_articles:
            continue

        lines.append("=" * 60)
        lines.append(section_name.upper())
        lines.append("=" * 60)
        lines.append("")

        for index, article in enumerate(section_articles, start=1):
            lines.append(f"{index}. {article.get('title', 'Sans titre')}")
            lines.append(f"Source : {article.get('source_label', 'Unknown')}")
            lines.append(f"Catégorie : {article.get('category', 'general')}")
            lines.append(f"Score : {article.get('score', 0)}")
            lines.append(f"Priorité IA : {article.get('ai_priority', 'unknown')}")
            lines.append("")
            lines.append(f"Résumé : {article.get('ai_summary', '')}")
            lines.append(f"Pourquoi c'est important : {article.get('ai_why_it_matters', '')}")
            lines.append(f"Lien : {article.get('url', '')}")
            lines.append("")

    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_to = os.getenv("MAIL_TO")

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = mail_to

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    print(f"Email envoyé à {mail_to}")


def main() -> None:
    articles = load_articles(INPUT_FILE)
    body = build_email_body(articles)
    send_email("Veille cyber quotidienne", body)


if __name__ == "__main__":
    main()