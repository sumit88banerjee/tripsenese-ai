import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.data_cleaning import load_and_clean
def main():
    df = load_and_clean(
    "data/raw/jaipur_places_raw.json",
    "data/processed/jaipur_places_clean.csv",
    )
    print(df.head())
    print(f"Cleaned rows: {len(df)}")
if __name__ == "__main__":
    main()  