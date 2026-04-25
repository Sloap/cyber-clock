import json
import re
from pathlib import Path
from openai import OpenAI
#from google import genai
from prompts import SYSTEM_PROMPT


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR.parent / "ressources" / "all_sources.json" #Fichier contenant les articles enrichis
OUTPUT_FILE = BASE_DIR.parent / "ressources" / "ai_summaries.json" #Fichier de sortie des résumés IA
client = OpenAI() #On définit openai comme api IA pour le résumé
#client = genai.Client()

def load_articles(path: Path) -> list[dict]: #Chargement des articles depuis le JSON généré par le collector
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_to_json(data: list[dict], path: Path) -> None: #Sauvegarde des résumés IA dans un fichier JSON
    path.parent.mkdir(parents=True, exist_ok=True) #Création du dossier ressources s'il n'existe pas

    with open(path, "w", encoding="utf-8") as f: #Ouverture du fichier pour écrire dedans
        json.dump(data, f, indent=4, ensure_ascii=False) #Ecriture des données dans le fichier

    print(f"Données sauvegardées dans {path}")

def clean_text(text: str, max_length: int = 1200) -> str: #Nettoyage basique du texte avant envoi à l'IA
    text = re.sub(r"<[^>]+>", " ", text) #Suppression des balises HTML
    text = re.sub(r"\s+", " ", text).strip() #Suppression des espaces multiples

    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text

def build_user_prompt(article: dict) -> str: #Construction du prompt utilisateur à envoyer au modèle
    clean_summary = clean_text(article.get("summary", ""))

    return f"""
Voici un article de veille cyber.

Source : {article.get('source_label', 'Unknown')}
Catégorie : {article.get('category', 'general')}
Titre : {article.get('title', 'Sans titre')}
Résumé brut : {clean_summary}

Donne une réponse JSON en français avec :
- ai_summary
- ai_priority
- ai_why_it_matters
""".strip()


def llm_call(article: dict) -> dict: #Appel réel à l'API IA pour résumer un article avec openai
    user_prompt = build_user_prompt(article)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    result_text = response.output_text
    return json.loads(result_text)




def summarize_articles(articles: list[dict]) -> list[dict]: #Ajout des champs IA à chaque article sélectionné
    summarized_articles = []

    for article in articles:
        user_prompt = build_user_prompt(article) #Construction du prompt pour le modèle

        #Affichage optionnel pour comprendre ce qui serait envoyé à l'IA
        print("-" * 60)
        print(f"Préparation du résumé IA pour : {article.get('title', 'Sans titre')}")
        print("-" * 60)

        llm_result = llm_call(article) #Simulation de la réponse IA

        enriched_article = article.copy() #Copie de l'article pour ne pas modifier l'original
        enriched_article["ai_summary"] = llm_result["ai_summary"]
        enriched_article["ai_priority"] = llm_result["ai_priority"]
        enriched_article["ai_why_it_matters"] = llm_result["ai_why_it_matters"]

        summarized_articles.append(enriched_article)

    return summarized_articles


def select_top_articles(articles: list[dict], limit: int = 5) -> list[dict]: #Sélection simple des meilleurs articles pour le résumé IA
    sorted_articles = sorted(articles, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_articles[:limit]

    


def main() -> None: #Point d'entrée du script de résumé IA
    articles = load_articles(INPUT_FILE) #Chargement des articles enrichis depuis le collector

    print(f"Nombre total d'articles chargés : {len(articles)}")

    top_articles = select_top_articles(articles, limit=10) #Sélection des 5 articles les plus importants
    print(f"Nombre d'articles sélectionnés pour résumé IA : {len(top_articles)}")

    summarized_articles = summarize_articles(top_articles) #Ajout des résumés IA

    save_to_json(summarized_articles, OUTPUT_FILE) #Sauvegarde dans un JSON dédié

    print("-" * 60)
    print("Aperçu des résumés IA :")

    for article in summarized_articles:
        print(f"Titre           : {article['title']}")
        print(f"Score           : {article['score']}")
        print(f"Catégorie       : {article['category']}")
        print(f"Résumé IA       : {article['ai_summary']}")
        print(f"Priorité IA     : {article['ai_priority']}")
        print(f"Pourquoi c'est important : {article['ai_why_it_matters']}")
        print("-" * 60)


if __name__ == "__main__":
    main()