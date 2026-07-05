import os
import time
import random
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


INCIDENT_KEYWORDS = [
    "fire",
    "accident",
    "stampede",
    "viral",
    "controversy",
    "scam",
    "tourist complaint",
    "safety",
    "crowd",
    "closed",
    "closure",
    "food poisoning",
    "hygiene",
    "protest",
    "ban",
    "flood",
    "emergency",
    "waterlogging",
    "traffic",
    "road closed",
    "train delay",
    "flight delay",
]


POSITIVE_KEYWORDS = [
    "award",
    "festival",
    "renovated",
    "heritage",
    "recommended",
    "popular",
    "must visit",
    "restored",
    "tourism boost",
    "new attraction",
    "reopened",
]


WEATHER_NEWS_KEYWORDS = [
    "rain",
    "rains",
    "rainfall",
    "heavy rain",
    "very heavy rain",
    "extremely heavy rain",
    "monsoon",
    "red alert",
    "orange alert",
    "yellow alert",
    "IMD",
    "BMC",
    "waterlogging",
    "flooding",
    "flood",
    "high tide",
    "local train",
    "flight delay",
    "traffic",
    "road closed",
]


DEFAULT_PLACE_ALIASES = {
    # Jaipur
    "amber palace": ["amber palace", "amer palace", "amber fort", "amer fort"],
    "amber fort": ["amber fort", "amer fort", "amber palace", "amer palace"],
    "amer fort": ["amer fort", "amber fort", "amber palace", "amer palace"],
    "hawa mahal": ["hawa mahal", "palace of winds"],
    "city palace": ["city palace jaipur", "city palace"],
    "jantar mantar": ["jantar mantar", "jantar mantar jaipur"],
    "jal mahal": ["jal mahal", "water palace"],
    "nahargarh fort": ["nahargarh fort", "nahargarh"],
    "jaigarh fort": ["jaigarh fort", "jaigarh"],
    "albert hall museum": ["albert hall museum", "albert hall"],
    "birla mandir": ["birla mandir", "lakshmi narayan temple"],
    "johari bazaar": ["johari bazaar", "johri bazar", "johri bazaar"],
    "bapu bazaar": ["bapu bazaar", "bapu market"],
    "lmb restaurant": ["lmb", "laxmi mishthan bhandar", "lmb restaurant"],
    "chokhi dhani": ["chokhi dhani"],

    # Mumbai
    "gateway of india": ["gateway of india"],
    "marine drive": ["marine drive", "queen's necklace", "queens necklace"],
    "juhu beach": ["juhu beach", "juhu"],
    "girgaon chowpatty": ["girgaon chowpatty", "chowpatty"],
    "siddhivinayak temple": ["siddhivinayak temple", "siddhivinayak"],
    "haji ali dargah": ["haji ali dargah", "haji ali"],
    "elephanta caves": ["elephanta caves", "elephanta"],
    "colaba causeway": ["colaba causeway", "colaba market"],
    "crawford market": ["crawford market"],
    "chor bazaar": ["chor bazaar"],
    "bandra worli sea link": ["bandra worli sea link", "sea link"],
    "bandstand": ["bandstand", "bandra bandstand"],
    "phoenix palladium": ["phoenix palladium", "palladium mall"],
}


def quote_if_needed(term: str) -> str:
    term = str(term).strip()
    if " " in term:
        return f'"{term}"'
    return term


def build_city_news_query(city: str) -> str:
    """
    Broad city-level GDELT query.

    This is intentionally not place-specific.
    We fetch city-level articles first, then match them locally
    against place names and aliases.
    """
    city = city.strip()

    general_terms = [
        "tourism",
        "tourist",
        "travel",
        "restaurant",
        "food",
        "market",
        "heritage",
        "museum",
        "temple",
        "fort",
        "palace",
        "beach",
        "festival",
        "incident",
        "safety",
        "viral",
        "crowd",
        "traffic",
    ]

    terms = " OR ".join(general_terms)
    return f'"{city}" ({terms})'


def build_city_weather_news_query(city: str) -> str:
    """
    City-level weather/disruption news query.

    This catches Mumbai rain / IMD alert / BMC warning type news,
    even when no specific tourist place is mentioned.
    """
    city = city.strip()

    terms = " OR ".join(
        quote_if_needed(keyword)
        for keyword in WEATHER_NEWS_KEYWORDS
    )

    return f'"{city}" ({terms})'


def gdelt_request(
    query: str,
    max_records: int,
    lookback_days: int,
) -> list[dict]:
    """
    Call public GDELT DOC 2.0 API.

    No API key is required.
    Retry logic handles temporary 429 rate limiting.
    """
    max_retries = int(os.getenv("GDELT_MAX_RETRIES", "5"))

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "sort": "HybridRel",
        "maxrecords": max_records,
        "timespan": f"{lookback_days}d",
    }

    headers = {
        "User-Agent": "TripSenseAI/1.0 educational hackathon project"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                GDELT_DOC_URL,
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(1, 3)
                print(f"GDELT rate limited. Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])

        except requests.exceptions.RequestException as exc:
            wait_time = (2 ** attempt) + random.uniform(1, 3)
            print(f"GDELT request failed: {exc}. Waiting {wait_time:.1f}s")
            time.sleep(wait_time)

    print("GDELT failed after retries.")
    return []


def normalize_text(value) -> str:
    if value is None:
        return ""

    return str(value).lower().strip()


def article_text(article: dict) -> str:
    """
    GDELT ArtList usually gives metadata, not full article body.
    So we match using title, URL, domain/source, and date fields.
    """
    parts = [
        article.get("title"),
        article.get("url"),
        article.get("url_mobile"),
        article.get("domain"),
        article.get("source"),
        article.get("seendate"),
        article.get("language"),
        article.get("sourcecountry"),
    ]

    return " ".join(normalize_text(part) for part in parts if part)


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    text = normalize_text(text)

    hits = []

    for keyword in keywords:
        keyword_lower = normalize_text(keyword)
        if keyword_lower and keyword_lower in text:
            hits.append(keyword)

    return hits


def load_aliases_from_csv(path: str = "data/config/place_aliases.csv") -> dict[str, list[str]]:
    """
    Optional CSV format:

    city,place_name,aliases
    Jaipur,Amber Palace,"amber palace|amer fort|amber fort"
    Mumbai,Marine Drive,"marine drive|queen's necklace|queens necklace"

    If the file is missing, hardcoded aliases are still used.
    """
    alias_path = Path(path)

    if not alias_path.exists():
        return {}

    alias_df = pd.read_csv(alias_path)

    required_columns = {"place_name", "aliases"}
    if not required_columns.issubset(set(alias_df.columns)):
        return {}

    alias_map = {}

    for _, row in alias_df.iterrows():
        place_name = normalize_text(row.get("place_name"))
        aliases_value = str(row.get("aliases", ""))

        aliases = [
            normalize_text(alias)
            for alias in aliases_value.split("|")
            if normalize_text(alias)
        ]

        if place_name and aliases:
            alias_map[place_name] = aliases

    return alias_map


def clean_place_name_for_alias(place_name: str) -> str:
    name = normalize_text(place_name)

    remove_words = [
        "restaurant",
        "hotel",
        "jaipur",
        "mumbai",
        "maharashtra",
        "rajasthan",
        "india",
    ]

    for word in remove_words:
        name = name.replace(word, "")

    name = " ".join(name.split())
    return name


def get_place_aliases(place_name: str) -> list[str]:
    name = normalize_text(place_name)
    cleaned_name = clean_place_name_for_alias(place_name)

    aliases = set()

    if name:
        aliases.add(name)

    if cleaned_name:
        aliases.add(cleaned_name)

    external_aliases = load_aliases_from_csv()

    combined_aliases = {}
    combined_aliases.update(DEFAULT_PLACE_ALIASES)
    combined_aliases.update(external_aliases)

    for key, values in combined_aliases.items():
        key_lower = normalize_text(key)

        if key_lower in name or name in key_lower or key_lower in cleaned_name:
            aliases.update(normalize_text(value) for value in values)

    # Remove very tiny aliases because they create false positives.
    aliases = {
        alias
        for alias in aliases
        if alias and len(alias) >= 3
    }

    return sorted(aliases)


def match_articles_to_places(
    places_df: pd.DataFrame,
    articles: list[dict],
    city: str,
) -> list[dict]:
    """
    Match city-level GDELT articles to place names.

    Important:
    This does NOT try to force city-wide rain news onto every place.
    City-wide rain warning should come from weather_intelligence.py.
    """
    matched_rows = []

    if places_df.empty or not articles:
        return matched_rows

    for _, place in places_df.iterrows():
        place_id = place.get("place_id")
        place_name = str(place.get("name", ""))
        aliases = get_place_aliases(place_name)

        if not aliases:
            continue

        for article in articles:
            text = article_text(article)

            matched_alias = None

            for alias in aliases:
                if alias and alias in text:
                    matched_alias = alias
                    break

            if not matched_alias:
                continue

            incident_hits = keyword_hits(text, INCIDENT_KEYWORDS + WEATHER_NEWS_KEYWORDS)
            positive_hits = keyword_hits(text, POSITIVE_KEYWORDS)

            matched_rows.append(
                {
                    "place_id": place_id,
                    "place_name": place_name,
                    "city": city,
                    "matched_alias": matched_alias,
                    "article_title": article.get("title"),
                    "article_url": article.get("url"),
                    "source": article.get("source") or article.get("domain"),
                    "published_date": article.get("seendate"),
                    "incident_keywords_found": ", ".join(incident_hits),
                    "positive_keywords_found": ", ".join(positive_hits),
                    "has_incident_signal": len(incident_hits) > 0,
                    "has_positive_signal": len(positive_hits) > 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return matched_rows


def summarize_news(
    matched_df: pd.DataFrame,
    places_df: pd.DataFrame,
    city: str,
) -> pd.DataFrame:
    """
    Always returns one row per selected place.

    So Streamlit can show:
    - Low news risk when no place-specific match exists
    - Medium/High when matched article signals exist
    """
    base_df = places_df[["place_id", "name"]].copy()
    base_df = base_df.rename(columns={"name": "place_name"})
    base_df["city"] = city

    output_columns = [
        "place_id",
        "place_name",
        "city",
        "news_count",
        "incident_count",
        "positive_count",
        "news_risk_level",
        "news_signal_score",
        "latest_article_title",
        "latest_article_url",
    ]

    if matched_df.empty:
        base_df["news_count"] = 0
        base_df["incident_count"] = 0
        base_df["positive_count"] = 0
        base_df["news_risk_level"] = "Low"
        base_df["news_signal_score"] = 0
        base_df["latest_article_title"] = ""
        base_df["latest_article_url"] = ""
        return base_df[output_columns]

    grouped_rows = []

    group_columns = ["place_id", "place_name", "city"]

    for (place_id, place_name, city_name), group in matched_df.groupby(
        group_columns,
        dropna=False,
    ):
        news_count = len(group)
        incident_count = int(group["has_incident_signal"].sum())
        positive_count = int(group["has_positive_signal"].sum())

        news_signal_score = min(
            100,
            news_count * 10 + incident_count * 25 + positive_count * 5,
        )

        if incident_count >= 2 or news_signal_score >= 70:
            news_risk_level = "High"
        elif incident_count == 1 or news_signal_score >= 35:
            news_risk_level = "Medium"
        else:
            news_risk_level = "Low"

        latest = group.iloc[0]

        grouped_rows.append(
            {
                "place_id": place_id,
                "place_name": place_name,
                "city": city_name,
                "news_count": news_count,
                "incident_count": incident_count,
                "positive_count": positive_count,
                "news_risk_level": news_risk_level,
                "news_signal_score": news_signal_score,
                "latest_article_title": latest.get("article_title", ""),
                "latest_article_url": latest.get("article_url", ""),
            }
        )

    summary_df = pd.DataFrame(grouped_rows)

    final_df = base_df.merge(
        summary_df,
        on=["place_id", "place_name", "city"],
        how="left",
    )

    final_df["news_count"] = final_df["news_count"].fillna(0).astype(int)
    final_df["incident_count"] = final_df["incident_count"].fillna(0).astype(int)
    final_df["positive_count"] = final_df["positive_count"].fillna(0).astype(int)
    final_df["news_risk_level"] = final_df["news_risk_level"].fillna("Low")
    final_df["news_signal_score"] = final_df["news_signal_score"].fillna(0).astype(int)
    final_df["latest_article_title"] = final_df["latest_article_title"].fillna("")
    final_df["latest_article_url"] = final_df["latest_article_url"].fillna("")

    return final_df[output_columns]