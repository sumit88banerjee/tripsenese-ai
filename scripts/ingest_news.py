import os
import sys
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.news_intelligence import (
    build_city_news_query,
    build_city_weather_news_query,
    gdelt_request,
    match_articles_to_places,
    summarize_news,
)

load_dotenv()


def parse_cities() -> list[str]:
    cities_value = os.getenv("TRIPSENSE_CITIES", "Jaipur,Mumbai")
    return [city.strip() for city in cities_value.split(",") if city.strip()]


def normalize_city(value) -> str:
    return str(value).strip().lower()


def city_slug(city: str) -> str:
    return (
        city.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def cache_is_fresh(cache_path: str, max_age_hours: int) -> bool:
    path = Path(cache_path)

    if not path.exists():
        return False

    if max_age_hours <= 0:
        return False

    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds < max_age_hours * 3600


def load_json(cache_path: str) -> list[dict]:
    with open(cache_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(cache_path: str, data: list[dict]) -> None:
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def dedupe_articles(articles: list[dict]) -> list[dict]:
    seen = set()
    output = []

    for article in articles:
        url = article.get("url")
        title = article.get("title")

        key = url or title

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        output.append(article)

    return output


def find_places_csv() -> Path:
    candidates = [
        Path("data/processed/all_cities_places_clean.csv"),
        Path("data/processed/tripsense_places_clean.csv"),
        Path("data/processed/jaipur_mumbai_places_clean.csv"),
        Path("data/processed/jaipur_places_clean.csv"),
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "No processed places CSV found. Run:\n"
        "python scripts/ingest_places.py\n"
        "python scripts/clean_places.py"
    )


def select_top_places_for_city(
    places_df: pd.DataFrame,
    city: str,
    top_n: int,
) -> pd.DataFrame:
    city_df = places_df[
        places_df["city"].apply(normalize_city) == normalize_city(city)
    ].copy()

    if city_df.empty:
        print(f"No places found for city: {city}")
        return city_df

    city_df["rating"] = city_df["rating"].fillna(0).astype(float)
    city_df["user_rating_count"] = (
        city_df["user_rating_count"]
        .fillna(0)
        .astype(float)
    )

    city_df["simple_rank_score"] = (
        city_df["rating"] * np.log1p(city_df["user_rating_count"].clip(lower=1))
    )

    return (
        city_df.sort_values("simple_rank_score", ascending=False)
        .head(top_n)
        .copy()
    )


def fetch_gdelt_articles_for_query(
    city: str,
    query_name: str,
    query: str,
    max_records: int,
    lookback_days: int,
    cache_hours: int,
) -> list[dict]:
    slug = city_slug(city)
    cache_path = f"data/raw/news/{slug}_{query_name}_gdelt_raw.json"

    if cache_is_fresh(cache_path, cache_hours):
        print(f"Using cached GDELT {query_name} news for {city}")
        return load_json(cache_path)

    print(f"Searching GDELT {query_name} news for {city}")
    print(f"Query: {query}")

    articles = gdelt_request(
        query=query,
        max_records=max_records,
        lookback_days=lookback_days,
    )

    save_json(cache_path, articles)

    return articles


def fetch_all_city_articles(
    city: str,
    max_records: int,
    lookback_days: int,
    cache_hours: int,
) -> list[dict]:
    general_query = build_city_news_query(city)
    weather_query = build_city_weather_news_query(city)

    general_articles = fetch_gdelt_articles_for_query(
        city=city,
        query_name="general",
        query=general_query,
        max_records=max_records,
        lookback_days=lookback_days,
        cache_hours=cache_hours,
    )

    weather_articles = fetch_gdelt_articles_for_query(
        city=city,
        query_name="weather_disruption",
        query=weather_query,
        max_records=max_records,
        lookback_days=lookback_days,
        cache_hours=cache_hours,
    )

    articles = general_articles + weather_articles
    articles = dedupe_articles(articles)

    print(f"{city}: total deduped GDELT articles = {len(articles)}")

    return articles


def main():
    places_csv = find_places_csv()

    matched_news_output = "data/processed/place_news.csv"
    summary_output = "data/processed/place_news_summary.csv"

    lookback_days = int(os.getenv("NEWS_LOOKBACK_DAYS", "14"))
    max_records = int(os.getenv("GDELT_MAX_RECORDS", "100"))
    top_n_places = int(os.getenv("NEWS_TOP_N_PLACES", "40"))
    cache_hours = int(os.getenv("NEWS_CACHE_HOURS", "24"))

    cities = parse_cities()

    print(f"Using places file: {places_csv}")
    print(f"Cities: {cities}")
    print(f"NEWS_LOOKBACK_DAYS={lookback_days}")
    print(f"GDELT_MAX_RECORDS={max_records}")
    print(f"NEWS_TOP_N_PLACES={top_n_places}")
    print(f"NEWS_CACHE_HOURS={cache_hours}")

    places_df = pd.read_csv(places_csv)

    if "city" not in places_df.columns:
        raise RuntimeError(
            "The places CSV must contain a `city` column for multi-city news ingestion."
        )

    all_matched_frames = []
    all_summary_frames = []

    for city in cities:
        print("\n" + "=" * 80)
        print(f"Processing news for city: {city}")
        print("=" * 80)

        top_places_df = select_top_places_for_city(
            places_df=places_df,
            city=city,
            top_n=top_n_places,
        )

        if top_places_df.empty:
            continue

        articles = fetch_all_city_articles(
            city=city,
            max_records=max_records,
            lookback_days=lookback_days,
            cache_hours=cache_hours,
        )

        matched_rows = match_articles_to_places(
            places_df=top_places_df,
            articles=articles,
            city=city,
        )

        matched_df = pd.DataFrame(matched_rows)

        if matched_df.empty:
            print(f"{city}: no place-specific GDELT matches found.")
        else:
            print(f"{city}: matched place-news rows = {len(matched_df)}")
            all_matched_frames.append(matched_df)

        summary_df = summarize_news(
            matched_df=matched_df,
            places_df=top_places_df,
            city=city,
        )

        print(f"{city}: summary rows = {len(summary_df)}")
        all_summary_frames.append(summary_df)

    Path("data/processed").mkdir(parents=True, exist_ok=True)

    if all_matched_frames:
        final_matched_df = pd.concat(all_matched_frames, ignore_index=True)
    else:
        final_matched_df = pd.DataFrame(
            columns=[
                "place_id",
                "place_name",
                "city",
                "matched_alias",
                "article_title",
                "article_url",
                "source",
                "published_date",
                "incident_keywords_found",
                "positive_keywords_found",
                "has_incident_signal",
                "has_positive_signal",
                "created_at",
            ]
        )

    if all_summary_frames:
        final_summary_df = pd.concat(all_summary_frames, ignore_index=True)
    else:
        final_summary_df = pd.DataFrame(
            columns=[
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
        )

    final_matched_df.to_csv(matched_news_output, index=False)
    final_summary_df.to_csv(summary_output, index=False)

    print("\n" + "=" * 80)
    print("News ingestion completed")
    print("=" * 80)
    print(f"Saved matched news: {matched_news_output}")
    print(f"Saved news summary: {summary_output}")
    print(f"Total matched rows: {len(final_matched_df)}")
    print(f"Total summary rows: {len(final_summary_df)}")


if __name__ == "__main__":
    main()