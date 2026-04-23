# Pulls top headlines by category from NewsAPI.org

import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_BASE = "https://newsapi.org/v2/top-headlines"


def get_headlines(categories: list[str], per_category: int = 5) -> dict:
    """
    Returns top headlines for each category from NewsAPI.

    Args:
        categories: list of category strings — valid options:
                    business, entertainment, general, health,
                    science, sports, technology
        per_category: number of headlines to fetch per category (default 5)

    Returns:
        {
            'technology': [
                {'title': '...', 'source': '...', 'url': '...'},
                ...
            ],
            ...
        }
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise EnvironmentError("NEWS_API_KEY not found — check your .env file")

    results = {}

    for category in categories:
        try:
            response = requests.get(
                NEWSAPI_BASE,
                params={
                    "apiKey": api_key,
                    "category": category,
                    "country": "us",
                    "pageSize": per_category,
                },
                timeout=10,
            )
            response.raise_for_status()
            articles = response.json().get("articles", [])

            results[category] = [
                {
                    "title": a.get("title", "No title"),
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "url": a.get("url", ""),
                }
                for a in articles
            ]

        except requests.exceptions.HTTPError as e:
            results[category] = {"error": f"HTTP {response.status_code}: {e}"}
        except requests.exceptions.RequestException as e:
            results[category] = {"error": f"Request failed: {e}"}

    return results


if __name__ == "__main__":
    categories = ["technology", "business", "general"]
    data = get_headlines(categories)

    for category, headlines in data.items():
        print(f"\n{category.upper()}")
        print("-" * 50)
        if isinstance(headlines, dict) and "error" in headlines:
            print(f"  ERROR: {headlines['error']}")
        else:
            for i, h in enumerate(headlines, 1):
                print(f"  {i}. {h['title']}")
                print(f"     {h['source']} — {h['url']}")
    print()
