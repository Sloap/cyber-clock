import feedparser


RSS_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml" #URL du flux RSS 


def fetch_feed(url: str) -> list[dict]: #Création de la fonction récupération des données
    feed = feedparser.parse(url) #Téléchargement du contenu du flux, parsing --> constante 
    articles = []

    for entry in feed.entries: #Récupération des infos. Unknown en cas d'échec (pour éviter un crash, il met automatiquement le fait que cela n'a pas été trouvé)
        article = { #Dictionnaire pour tout stocker
            "source": feed.feed.get("title", "Unknown"), 
            "title": entry.get("title", "Sans titre"), 
            "url": entry.get("link", "Pas de lien"),
            "published": entry.get("published", "Pas de date"),
        }
        articles.append(article)

    return articles


def main() -> None: #Fonction main qui récupère les données de la fonction fetch_feed pour les print 
    articles = fetch_feed(RSS_URL)

    print(f"Nombre d'articles structurés : {len(articles)}")
    print("-" * 60)

    for article in articles[:5]: #Boucle pour afficher de manière structurée la source, le titre, la date, et le lien de l'article
        print(f"Source : {article['source']}")
        print(f"Titre  : {article['title']}")
        print(f"Date   : {article['published']}")
        print(f"Lien   : {article['url']}")
        print("-" * 60)


if __name__ == "__main__":
    main()