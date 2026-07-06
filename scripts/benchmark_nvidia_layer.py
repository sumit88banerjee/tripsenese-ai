import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.gpu_accel import install_gpu_acceleration
ACCELERATION_MODE = install_gpu_acceleration()

import csv
import numpy as np
import pandas as pd


def benchmark_scoring(repeat: int = 5000) -> dict:
    input_path = Path("data/processed/top_places_news_weather_aware_gpu.csv")

    if not input_path.exists():
        input_path = Path("data/processed/all_cities_places_clean.csv")

    start = time.perf_counter()

    df = pd.read_csv(input_path)

    original_rows = len(df)

    df_big = pd.concat([df] * repeat, ignore_index=True)

    if "rating" not in df_big.columns:
        df_big["rating"] = 4.0

    if "user_rating_count" not in df_big.columns:
        df_big["user_rating_count"] = 100

    if "news_penalty" not in df_big.columns:
        df_big["news_penalty"] = 0.0

    if "weather_penalty" not in df_big.columns:
        df_big["weather_penalty"] = 0.0

    df_big["rating"] = df_big["rating"].fillna(0)
    df_big["user_rating_count"] = df_big["user_rating_count"].fillna(0)
    df_big["news_penalty"] = df_big["news_penalty"].fillna(0)
    df_big["weather_penalty"] = df_big["weather_penalty"].fillna(0)

    df_big["benchmark_score"] = (
        df_big["rating"] * np.log1p(df_big["user_rating_count"])
        - df_big["news_penalty"]
        - df_big["weather_penalty"]
    )

    if "city" in df_big.columns:
        result = (
            df_big.sort_values("benchmark_score", ascending=False)
            .groupby("city")
            .head(20)
        )
    else:
        result = df_big.sort_values("benchmark_score", ascending=False).head(40)

    elapsed = time.perf_counter() - start

    return {
        "acceleration_mode": ACCELERATION_MODE,
        "original_rows": original_rows,
        "benchmark_rows": len(df_big),
        "result_rows": len(result),
        "elapsed_seconds": round(elapsed, 4),
    }


def main():
    repeat = int(os.getenv("BENCHMARK_REPEAT", "5000"))
    result = benchmark_scoring(repeat=repeat)

    output_path = Path("data/processed/nvidia_benchmark_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)

    print(result)
    print(f"Saved benchmark result to {output_path}")


if __name__ == "__main__":
    main()