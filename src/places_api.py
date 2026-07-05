import os
import requests
from dotenv import load_dotenv

load_dotenv()

TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.location,"
    "places.rating,"
    "places.userRatingCount,"
    "places.priceLevel,"
    "places.primaryType,"
    "places.googleMapsUri"
)


def text_search(query: str, city: str, max_results: int = 20) -> list[dict]:
    """Run one Google Places Text Search request for one city/query."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is missing. Add it to .env")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    payload = {
        "textQuery": f"{query} in {city}",
        "maxResultCount": max_results,
        "languageCode": "en",
        "regionCode": "IN",
    }

    response = requests.post(TEXT_SEARCH_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json().get("places", [])
