import json
from pathlib import Path
import pandas as pd


def normalize_places(raw_places: list[dict]) -> pd.DataFrame:
    rows = []

    for place in raw_places:
        display_name = place.get("displayName", {}) or {}
        location = place.get("location", {}) or {}
        rows.append(
            {
                "place_id": place.get("id"),
                "name": display_name.get("text"),
                "city": place.get("_city"),
                "query_category": place.get("_query_category"),
                "source_query": place.get("_source_query"),
                "primary_type": place.get("primaryType"),
                "address": place.get("formattedAddress"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "rating": place.get("rating", 0),
                "user_rating_count": place.get("userRatingCount", 0),
                "price_level": place.get("priceLevel"),
                "google_maps_uri": place.get("googleMapsUri"),
                "is_food": place.get("_query_category") == "food",
                "is_tourist_spot": place.get("_query_category") == "tourist_spot",
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.dropna(subset=["place_id", "name", "city", "latitude", "longitude"])
    df = df.drop_duplicates(subset=["place_id"])
    df["rating"] = df["rating"].fillna(0).astype(float)
    df["user_rating_count"] = df["user_rating_count"].fillna(0).astype(int)
    df["price_level"] = df["price_level"].fillna("PRICE_LEVEL_MODERATE")
    return df


def load_and_clean(input_path: str, output_path: str) -> pd.DataFrame:
    with open(input_path, "r", encoding="utf-8") as f:
        raw_places = json.load(f)

    df = normalize_places(raw_places)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df
