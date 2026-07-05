import json
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import get_cities, slugify
from src.places_api import text_search

PLACE_QUERIES = [
    ("tourist_spot", "best tourist attractions"),
    ("tourist_spot", "popular places to visit"),
    ("tourist_spot", "historical places"),
    ("tourist_spot", "shopping markets"),
    ("food", "best local food restaurants"),
    ("food", "best street food"),
    ("food", "best cafes"),
    ("food", "best fine dining restaurants"),
]


def main() -> None:
    cities = get_cities()
    max_results = int(os.getenv("PLACES_MAX_RESULTS", "20"))
    all_places: list[dict] = []

    Path("data/raw").mkdir(parents=True, exist_ok=True)

    for city in cities:
        city_places: list[dict] = []
        print(f"\n=== Fetching Places for {city} ===")

        for category, query in PLACE_QUERIES:
            print(f"Fetching: {query} in {city}")
            places = text_search(query=query, city=city, max_results=max_results)

            for place in places:
                place["_query_category"] = category
                place["_city"] = city
                place["_source_query"] = query
                city_places.append(place)
                all_places.append(place)

            time.sleep(0.5)

        city_output = f"data/raw/{slugify(city)}_places_raw.json"
        with open(city_output, "w", encoding="utf-8") as f:
            json.dump(city_places, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(city_places)} raw places to {city_output}")

    output_path = "data/raw/all_places_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_places, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_places)} total raw places to {output_path}")


if __name__ == "__main__":
    main()
