import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.benchmark import benchmark_scoring


result = benchmark_scoring(
    "data/processed/jaipur_places_clean.csv",
    repeat=5000,
)

print("CPU pandas benchmark")
print(result)