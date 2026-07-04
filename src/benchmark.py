import time
import pandas as pd
from src.scoring import score_places
def make_large_dataset(df: pd.DataFrame, repeat: int = 5000) -> pd.DataFrame:
    large_df = pd.concat([df] * repeat, ignore_index=True)
    large_df["synthetic_id"] = range(len(large_df))
    return large_df
def benchmark_scoring(csv_path: str, repeat: int = 5000) -> dict:
    df = pd.read_csv(csv_path)
    large_df = make_large_dataset(df, repeat=repeat)
    start = time.perf_counter()
    scored = score_places(large_df, budget_type="budget")
    elapsed = time.perf_counter() - start
    return {
        "rows": len(large_df),
        "seconds": elapsed,
        "top_place": scored.iloc[0]["name"],
    }