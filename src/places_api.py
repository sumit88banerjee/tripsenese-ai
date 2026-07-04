import os
import requests
from dotenv import load_dotenv
load_dotenv()
TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
def text_search(query: str, city: str, max_results: int = 20) -> list[dict]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is missing. Add it to .env")
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.rating,"
            "places.userRatingCount,"
            "places.priceLevel,"
            "places.primaryType,"
            "places.googleMapsUri"
        ),
    }
    payload = {
        "textQuery": f"{query} in {city}",
        "maxResultCount": max_results,
        "languageCode": "en",
        "regionCode": "IN",
    }
    response = requests.post(
        TEXT_SEARCH_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )
    if not response.ok:
        print("Google Places API error")
        print("Status:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()
    return response.json().get("places", [])