import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.gpu_accel import install_gpu_acceleration
ACCELERATION_MODE = install_gpu_acceleration()

import numpy as np
import pandas as pd


DATA_DIR = Path("data/processed")


def is_outdoor_sensitive_vectorized(df: pd.DataFrame) -> pd.Series:
    keywords = [
        "beach", "marine drive", "chowpatty", "fort", "bazaar", "market",
        "garden", "lake", "ghat", "park", "waterfront", "sea link",
        "palace", "viewpoint", "zoo", "trail", "caves"
    ]

    name = df.get("name", "").fillna("").astype(str).str.lower()
    primary_type = df.get("primary_type", "").fillna("").astype(str).str.lower()
    query_category = df.get("query_category", "").fillna("").astype(str).str.lower()

    keyword_pattern = "|".join(keywords)

    return (
        name.str.contains(keyword_pattern, regex=True)
        | primary_type.str.contains("park|tourist_attraction", regex=True)
        | query_category.eq("tourist_spot")
    )


def build_ranked_table() -> pd.DataFrame:
    places_path = DATA_DIR / "all_cities_places_clean.csv"
    news_path = DATA_DIR / "place_news_summary.csv"
    weather_path = DATA_DIR / "city_weather_summary.csv"

    places = pd.read_csv(places_path)
    news = pd.read_csv(news_path)
    weather = pd.read_csv(weather_path)

    places["city_key"] = places["city"].fillna("").astype(str).str.lower()
    weather["city_key"] = weather["city"].fillna("").astype(str).str.lower()

    dashboard = places.merge(
        news,
        how="left",
        on="place_id"
    ).merge(
        weather,
        how="left",
        on="city_key",
        suffixes=("", "_weather")
    )

    dashboard["news_risk_level"] = dashboard["news_risk_level"].fillna("Low")
    dashboard["weather_risk_level"] = dashboard["weather_risk_level"].fillna("Low")
    dashboard["primary_weather_risk"] = dashboard["primary_weather_risk"].fillna("None")

    dashboard["rating"] = dashboard["rating"].fillna(0)
    dashboard["user_rating_count"] = dashboard["user_rating_count"].fillna(0)

    dashboard["outdoor_weather_sensitive"] = is_outdoor_sensitive_vectorized(dashboard)

    dashboard["simple_popularity_score"] = (
        dashboard["rating"] * np.log1p(dashboard["user_rating_count"])
    )

    dashboard["news_penalty"] = 0.0
    dashboard.loc[dashboard["news_risk_level"].eq("High"), "news_penalty"] = 0.15
    dashboard.loc[dashboard["news_risk_level"].eq("Medium"), "news_penalty"] = 0.08

    dashboard["weather_penalty"] = 0.0

    high_weather = dashboard["weather_risk_level"].eq("High")
    medium_weather = dashboard["weather_risk_level"].eq("Medium")
    outdoor = dashboard["outdoor_weather_sensitive"].eq(True)

    dashboard.loc[high_weather & outdoor, "weather_penalty"] = 0.22
    dashboard.loc[medium_weather & outdoor, "weather_penalty"] = 0.12
    dashboard.loc[high_weather & ~outdoor, "weather_penalty"] = 0.06
    dashboard.loc[medium_weather & ~outdoor, "weather_penalty"] = 0.03

    dashboard["news_weather_adjusted_score"] = (
        dashboard["simple_popularity_score"]
        - dashboard["news_penalty"]
        - dashboard["weather_penalty"]
    )

    ranked = dashboard.sort_values(
        "news_weather_adjusted_score",
        ascending=False
    )

    return ranked


def main():
    start = time.perf_counter()

    ranked = build_ranked_table()

    output_path = DATA_DIR / "top_places_news_weather_aware_gpu.csv"
    ranked.to_csv(output_path, index=False)

    elapsed = time.perf_counter() - start

    print(f"Acceleration mode: {ACCELERATION_MODE}")
    print(f"Rows ranked: {len(ranked)}")
    print(f"Saved: {output_path}")
    print(f"Elapsed seconds: {elapsed:.4f}")


if __name__ == "__main__":
    main()