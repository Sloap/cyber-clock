import feedparser
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCES_FILE = BASE_DIR / "sources.json" #Fichier de configuration des sources
OUTPUT_DIR = BASE_DIR.parent / "ressources" #Dossier de stockage des fichiers JSON


def load_sources(path: Path) -> list[dict]: #Chargement des sources depuis un fichier JSON
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_feed(source: dict) -> list[dict]: #Création de la fonction récupération des données (adaptée multi-sources)
    feed = feedparser.parse(source["url"]) #Téléchargement du contenu du flux, parsing
    articles = []

    for entry in feed.entries: #Récupération des infos. Unknown en cas d'échec
        article = { #Dictionnaire pour tout stocker
            "source_name": source["name"],
            "source_label": source["label"],
            "feed_title": feed.feed.get("title", "Unknown"),
            "title": entry.get("title", "Sans titre"),
            "url": entry.get("link", "Pas de lien"),
            "published": entry.get("published", "Pas de date"),
            "summary": entry.get("summary", ""), #Résumé brut fourni par certains flux
        }
        articles.append(article)

    return articles

def save_to_json(data: list[dict], filename: str = "all_sources.json") -> None:
    path = OUTPUT_DIR / filename #Création du path pour les datas dans le dossier ressources
    path.parent.mkdir(parents=True, exist_ok=True) #Création du dossier ressources s'il n'existe pas

    with open(path, "w", encoding="utf-8") as f: #Ouverture du fichier pour écrire dedans
        json.dump(data, f, indent=4, ensure_ascii=False) #Ecriture des données dans le fichier

    print(f"Données sauvegardées dans {path}")

def deduplicate_articles(articles: list[dict]) -> list[dict]: #Fonction de suppression des doublons
    seen_urls = set()
    seen_titles = set()
    unique_articles = []

    for article in articles:
        url = article["url"]
        title = article["title"].strip().lower()

        #Si l'URL ou le titre a déjà été vu → on skip
        if url in seen_urls or title in seen_titles:
            continue

        seen_urls.add(url)
        seen_titles.add(title)
        unique_articles.append(article)

    return unique_articles

def categorize_article(article: dict) -> str: #Fonction de catégorisation des articles
    text = f"{article['title']} {article.get('summary', '')}".lower()

    #Catégorie ransomware / rançongiciel
    if "ransomware" in text or "rançongiciel" in text:
        return "ransomware"

    #Catégorie fuite de données / data breach
    if "breach" in text or "leak" in text or "fuite de données" in text or "data leak" in text:
        return "data_breach"

    #Catégorie vulnérabilité / CVE / faille
    if (
        "vulnerability" in text
        or "vulnérabilité" in text
        or "faille" in text
        or "cve-" in text
        or "zero-day" in text
        or "0-day" in text
    ):
        return "vulnerability"

    #Catégorie malware
    if "malware" in text or "trojan" in text or "loader" in text or "botnet" in text:
        return "malware"

    #Catégorie incident / attaque
    if (
        "cyberattack" in text
        or "cyber attack" in text
        or "cyberattaque" in text
        or "attaque" in text
        or "incident" in text
        or "compromise" in text
        or "compromission" in text
    ):
        return "incident"

    #Catégorie réglementation / autorités / conformité
    if (
        "anssi" in text
        or "cert" in text
        or "regulation" in text
        or "directive" in text
        or "compliance" in text
        or "conformité" in text
    ):
        return "regulation"

    return "general"

def score_article(article: dict) -> int: #Fonction de scoring des articles
    score = 0
    text = f"{article['title']} {article.get('summary', '')}".lower()

    #Score basé sur mots-clés critiques EN / FR
    if "ransomware" in text or "rançongiciel" in text:
        score += 4

    if "0-day" in text or "zero-day" in text:
        score += 4

    if "vulnerability" in text or "vulnérabilité" in text or "faille" in text:
        score += 3

    if "cve-" in text or "cve" in text:
        score += 3

    if "breach" in text or "leak" in text or "fuite de données" in text:
        score += 3

    if "cyberattack" in text or "cyber attack" in text or "cyberattaque" in text or "attaque" in text:
        score += 2

    if "malware" in text or "trojan" in text or "botnet" in text:
        score += 2

    if "anssi" in text or "cert-fr" in text or "cisa" in text:
        score += 2

    #Score basé sur la source
    if article["source_name"] in ["cisa", "cert-fr", "bleepingcomputer", "thehackernews", "therecord"]:
        score += 2
    elif article["source_name"] in ["krebsonsecurity", "theregister-security", "zdnet-fr", "arstechnica"]:
        score += 1

    return score

def enrich_articles(articles: list[dict]) -> list[dict]: #Ajout du score et de la catégorie à chaque article
    for article in articles:
        article["category"] = categorize_article(article)
        article["score"] = score_article(article)

    return articles

def select_top_articles(articles: list[dict], limit: int = 10) -> list[dict]: #Sélection d'un top plus varié
    selected_articles = []
    source_counts = {}
    seen_patterns = set()

    for article in articles:
        source_name = article["source_name"]
        title = article["title"].lower()

        #Création d'un pattern simple pour éviter certains titres trop répétitifs
        if "known exploited vulnerabilit" in title and "catalog" in title:
            title_pattern = "cisa_known_exploited_catalog"
        else:
            title_pattern = title

        #Limite du nombre d'articles par source dans le top
        if source_counts.get(source_name, 0) >= 2:
            continue

        #Évite les articles trop répétitifs dans le top
        if title_pattern in seen_patterns:
            continue

        selected_articles.append(article)
        source_counts[source_name] = source_counts.get(source_name, 0) + 1
        seen_patterns.add(title_pattern)

        if len(selected_articles) >= limit:
            break

    return selected_articles

def main() -> None: #Fonction main qui récupère les données de toutes les sources
    sources = load_sources(SOURCES_FILE) #Chargement des sources
    all_articles = []

    for source in sources: #Boucle sur chaque source
        print(f"Collecte de la source : {source['label']}")
        articles = fetch_feed(source)
        print(f"-> {len(articles)} article(s) récupéré(s)")
        all_articles.extend(articles) #Ajout à la liste globale

    print(f"Nombre total d'articles AVANT déduplication : {len(all_articles)}")

    unique_articles = deduplicate_articles(all_articles)

    print(f"Nombre total d'articles APRÈS déduplication : {len(unique_articles)}")

    enriched_articles = enrich_articles(unique_articles) #Ajout des scores et catégories

    #Tri par score décroissant
    enriched_articles.sort(key=lambda x: x["score"], reverse=True)

    top_articles = select_top_articles(enriched_articles, limit=10) #Sélection finale plus variée

    save_to_json(enriched_articles, "all_sources.json") #Sauvegarde globale

    print("-" * 60)
    print("Top 10 articles les plus importants :")

    for article in top_articles: #Boucle pour afficher un aperçu des articles les plus importants
        print(f"[Score {article['score']}] [{article['category']}] {article['title']}")
        print(f"Source : {article['source_label']}")
        print(f"Date   : {article['published']}")
        print(f"Lien   : {article['url']}")
        print("-" * 60)


if __name__ == "__main__":
    main()