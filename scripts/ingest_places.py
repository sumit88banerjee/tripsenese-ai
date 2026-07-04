import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.places_api import text_search
CITY = "Jaipur"
QUERIES = [
 ("tourist_spot", "best tourist attractions"),
    ("tourist_spot", "historical places"),
    ("tourist_spot", "shopping markets"),
    ("food", "best local food restaurants"),
    ("food", "best street food"),
    ("food", "best luxury restaurants"),
]
def main():
    output = []
    for category, query in QUERIES:
        print(f"Fetching: {query} in {CITY}")
        places = text_search(query=query, city=CITY, max_results=20)
        for place in places:
            place["_query_category"] = category
            place["_city"] = CITY
            place["_source_query"] = query
            output.append(place)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    output_path = "data/raw/jaipur_places_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(output)} places to {output_path}")
if __name__ == "__main__":
    main()