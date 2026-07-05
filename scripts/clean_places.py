import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data_cleaning import load_and_clean


def main():
    input_path = "data/raw/all_cities_places_raw.json"
    output_path = "data/processed/all_cities_places_clean.csv"

    if not Path(input_path).exists():
        raise FileNotFoundError(
            f"{input_path} not found. Run: python scripts/ingest_places.py"
        )

    df = load_and_clean(
        input_path=input_path,
        output_path=output_path,
    )

    print(df.head())
    print("\nRows by city:")
    print(df["city"].value_counts())

    print("\nRows by city/category:")
    print(df.groupby(["city", "query_category"]).size())

    print(f"\nCleaned rows: {len(df)}")
    print(f"Saved cleaned multi-city data to {output_path}")


if __name__ == "__main__":
    main()