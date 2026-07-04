import numpy as np
import pandas as pd
PRICE_MAP = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}
def normalize_series(s: pd.Series) -> pd.Series:
    if len(s) == 0:
        return s
    if s.max() == s.min():
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min())
def add_price_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_numeric"] = df["price_level"].map(PRICE_MAP).fillna(2)
    return df
def score_places(df: pd.DataFrame, budget_type: str = "budget") -> pd.DataFrame:
    df = df.copy()
    df = add_price_numeric(df)
    df["rating"] = df["rating"].fillna(0).astype(float)
    df["user_rating_count"] = df["user_rating_count"].fillna(0).astype(int)
    df["rating_score"] = df["rating"] / 5.0
    df["popularity_score"] = normalize_series(np.log1p(df["user_rating_count"]))
    if budget_type == "budget":
        df["budget_score"] = 1 - (df["price_numeric"] / 4)
    elif budget_type == "luxury":
        df["budget_score"] = df["price_numeric"] / 4
    else:
        df["budget_score"] = 0.6
    df["final_score"] = (
        0.45 * df["rating_score"]
        + 0.35 * df["popularity_score"]
        + 0.20 * df["budget_score"]
    )
    return df.sort_values("final_score", ascending=False)