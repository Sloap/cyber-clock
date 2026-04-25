import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR.parent / "ressources" / "ai_summaries.json"

PRIORITY_COLORS = {
    "high":   "#cf222e",
    "medium": "#9a6700",
    "low":    "#1a7f37",
}
PRIORITY_LABELS = {
    "high":   "Haute",
    "medium": "Moyenne",
    "low":    "Faible",
}
CATEGORY_LABELS = {
    "ransomware":   "Ransomware",
    "data_breach":  "Fuite de données",
    "vulnerability":"Vulnérabilité",
    "malware":      "Malware",
    "incident":     "Incident",
    "regulation":   "Réglementation",
    "general":      "Général",
}


def load_articles(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_article_card(article: dict, index: int) -> str:
    title    = article.get("title", "Sans titre")
    source   = article.get("source_label", "Unknown")
    category = article.get("category", "general")
    priority = article.get("ai_priority", "medium").lower()
    summary  = article.get("ai_summary", "")
    why      = article.get("ai_why_it_matters", "")
    url      = article.get("url", "#")

    color         = PRIORITY_COLORS.get(priority, "#8b949e")
    priority_label = PRIORITY_LABELS.get(priority, priority.capitalize())
    category_label = CATEGORY_LABELS.get(category, category.capitalize())

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
  <tr>
    <td style="background:#ffffff;border-radius:6px;border:1px solid #d0d7de;border-left:3px solid {color};padding:16px 20px;">

      <div style="font-size:14px;font-weight:700;color:#24292f;line-height:1.4;margin-bottom:10px;">
        {index}. {title}
      </div>

      <table cellpadding="0" cellspacing="4" style="margin-bottom:12px;">
        <tr>
          <td>
            <span style="display:inline-block;background:#f6f8fa;color:#57606a;font-size:11px;padding:2px 8px;border-radius:4px;border:1px solid #d0d7de;">
              {source}
            </span>
          </td>
          <td style="padding-left:6px;">
            <span style="display:inline-block;background:#f6f8fa;color:#57606a;font-size:11px;padding:2px 8px;border-radius:4px;border:1px solid #d0d7de;">
              {category_label}
            </span>
          </td>
          <td style="padding-left:6px;">
            <span style="display:inline-block;background:#ffffff;color:{color};font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;border:1px solid {color};">
              Priorité : {priority_label}
            </span>
          </td>
        </tr>
      </table>

      <div style="font-size:13px;color:#24292f;line-height:1.6;margin-bottom:12px;">
        {summary}
      </div>

      <div style="background:#f6f8fa;border-radius:6px;border:1px solid #d0d7de;padding:10px 14px;margin-bottom:14px;">
        <div style="font-size:10px;font-weight:700;color:#0969da;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;">
          Pourquoi c'est important
        </div>
        <div style="font-size:12px;color:#57606a;line-height:1.5;">
          {why}
        </div>
      </div>

      <a href="{url}"
         style="display:inline-block;background:#0969da;color:#ffffff;font-size:12px;font-weight:600;
                padding:7px 16px;border-radius:6px;text-decoration:none;letter-spacing:0.3px;">
        Lire l'article &rarr;
      </a>

    </td>
  </tr>
</table>
"""


def build_section_html(name: str, articles: list[dict]) -> str:
    if not articles:
        return ""
    cards = "".join(build_article_card(a, i) for i, a in enumerate(articles, 1))
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
  <tr>
    <td style="padding-bottom:14px;">
      <div style="font-size:11px;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:1.2px;">
        {name}
      </div>
      <div style="height:1px;background:#d0d7de;margin-top:8px;"></div>
    </td>
  </tr>
  <tr>
    <td>{cards}</td>
  </tr>
</table>
"""


def build_email_html(articles: list[dict]) -> str:
    today = datetime.now().strftime("%d %B %Y")

    sections_data: dict[str, list[dict]] = {
        "Nouvelles vulnérabilités": [],
        "Articles importants": [],
    }
    for article in articles:
        section = article.get("section", "Articles importants")
        sections_data.setdefault(section, []).append(article)

    body_sections = (
        build_section_html("Nouvelles vulnérabilités", sections_data["Nouvelles vulnérabilités"])
        + build_section_html("Articles importants", sections_data["Articles importants"])
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Veille Cyber</title>
</head>
<body style="margin:0;padding:0;background:#f6f8fa;font-family:'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f8fa;padding:32px 16px;">
  <tr>
    <td align="center">
      <table width="600" cellpadding="0" cellspacing="0">

        <!-- En-tête -->
        <tr>
          <td style="background:#ffffff;border-top:3px solid #0969da;border:1px solid #d0d7de;
                     border-top:3px solid #0969da;border-radius:6px 6px 0 0;padding:22px 30px 18px;">
            <div style="font-size:18px;font-weight:700;color:#0969da;letter-spacing:1px;">
              Cyber Watch
            </div>
            <div style="font-size:12px;color:#57606a;margin-top:5px;">
              Veille quotidienne &mdash; {today}
            </div>
          </td>
        </tr>

        <!-- Contenu -->
        <tr>
          <td style="background:#f6f8fa;padding:24px 30px;border-left:1px solid #d0d7de;border-right:1px solid #d0d7de;">
            {body_sections}
          </td>
        </tr>

        <!-- Pied de page -->
        <tr>
          <td style="background:#ffffff;border-radius:0 0 6px 6px;border:1px solid #d0d7de;
                     border-top:1px solid #d0d7de;padding:14px 30px;">
            <div style="font-size:11px;color:#8c959f;text-align:center;">
              Généré automatiquement par Cyber Watch &middot; {today}
            </div>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

</body>
</html>"""


def build_email_body(articles: list[dict]) -> str:
    sections: dict[str, list[dict]] = {
        "Nouvelles vulnérabilités": [],
        "Articles importants": [],
    }
    for article in articles:
        section = article.get("section", "Articles importants")
        sections.setdefault(section, []).append(article)

    lines = ["Bonjour,", "", "Voici ta veille cyber du jour :", ""]

    for section_name, section_articles in sections.items():
        if not section_articles:
            continue
        lines += ["=" * 60, section_name.upper(), "=" * 60, ""]
        for i, article in enumerate(section_articles, 1):
            lines.append(f"{i}. {article.get('title', 'Sans titre')}")
            lines.append(f"Source    : {article.get('source_label', 'Unknown')}")
            lines.append(f"Catégorie : {article.get('category', 'general')}")
            lines.append(f"Priorité  : {article.get('ai_priority', 'unknown')}")
            lines.append("")
            lines.append(f"Résumé : {article.get('ai_summary', '')}")
            lines.append(f"Pourquoi c'est important : {article.get('ai_why_it_matters', '')}")
            lines.append(f"Lien : {article.get('url', '')}")
            lines.append("")

    return "\n".join(lines)


def send_email(subject: str, html_body: str, plain_body: str) -> None:
    smtp_host     = os.getenv("SMTP_HOST")
    smtp_port     = int(os.getenv("SMTP_PORT", "587"))
    smtp_user     = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_to       = os.getenv("MAIL_TO")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"]    = smtp_user
    message["To"]      = mail_to

    message.attach(MIMEText(plain_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body,  "html",  "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    print(f"Email envoyé à {mail_to}")


def main() -> None:
    articles   = load_articles(INPUT_FILE)
    html_body  = build_email_html(articles)
    plain_body = build_email_body(articles)
    send_email("Veille Cyber — Quotidienne", html_body, plain_body)


if __name__ == "__main__":
    main()
