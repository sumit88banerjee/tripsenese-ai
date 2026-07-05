import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.weather_intelligence import build_weather_summary_for_cities

load_dotenv()


def parse_cities() -> list[str]:
    cities_value = os.getenv("TRIPSENSE_CITIES", "Jaipur,Mumbai")
    return [city.strip() for city in cities_value.split(",") if city.strip()]


def main():
    output_path = "data/processed/city_weather_summary.csv"
    cities = parse_cities()
    summary_df = build_weather_summary_for_cities(cities)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    print(summary_df)
    print(f"Saved advanced weather summary to {output_path}")


if __name__ == "__main__":
    main()
