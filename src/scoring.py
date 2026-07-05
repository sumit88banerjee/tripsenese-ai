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


def normalize_risk(value) -> str:
    value = str(value or "Low").strip().lower()

    if value == "high":
        return "High"

    if value == "medium":
        return "Medium"

    return "Low"


def add_price_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_numeric"] = df["price_level"].map(PRICE_MAP).fillna(2)
    return df


def risk_penalty(
    risk,
    low: float = 0.0,
    medium: float = 0.05,
    high: float = 0.10,
) -> float:
    risk = normalize_risk(risk)

    if risk == "High":
        return high

    if risk == "Medium":
        return medium

    return low


def is_outdoor_weather_sensitive(row) -> bool:
    name = str(row.get("name", "")).lower()
    primary_type = str(row.get("primary_type", "")).lower()
    query_category = str(row.get("query_category", "")).lower()

    outdoor_keywords = [
        "beach",
        "marine drive",
        "chowpatty",
        "fort",
        "bazaar",
        "market",
        "garden",
        "lake",
        "ghat",
        "park",
        "waterfront",
        "sea link",
        "promenade",
        "drive",
        "caves",
        "palace",
        "mahal",
        "temple",
        "dargah",
        "monument",
        "zoo",
        "view point",
        "viewpoint",
    ]

    indoor_keywords = [
        "mall",
        "museum",
        "restaurant",
        "cafe",
        "hotel",
        "cinema",
        "theatre",
        "gallery",
    ]

    if any(keyword in name for keyword in indoor_keywords):
        return False

    if any(keyword in name for keyword in outdoor_keywords):
        return True

    if any(keyword in primary_type for keyword in ["park", "tourist_attraction"]):
        return True

    if query_category == "tourist_spot":
        return True

    return False


def ensure_risk_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    defaults = {
        "news_risk_level": "Low",
        "weather_risk_level": "Low",
        "rain_risk_level": "Low",
        "heat_risk_level": "Low",
        "wind_risk_level": "Low",
        "air_quality_risk_level": "Low",
        "uv_risk_level": "Low",
        "visibility_risk_level": "Low",
        "primary_weather_risk": "None",
    }

    for col, default_value in defaults.items():
        if col not in df.columns:
            df[col] = default_value

        df[col] = df[col].fillna(default_value).apply(normalize_risk) if col.endswith("_risk_level") else df[col].fillna(default_value)

    if "outdoor_weather_sensitive" not in df.columns:
        df["outdoor_weather_sensitive"] = df.apply(is_outdoor_weather_sensitive, axis=1)

    return df


def score_places(df: pd.DataFrame, budget_type: str = "budget") -> pd.DataFrame:
    df = df.copy()
    df = add_price_numeric(df)
    df = ensure_risk_columns(df)

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

    df["news_penalty"] = df["news_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.08,
            high=0.15,
        )
    )

    df["rain_penalty"] = df["rain_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.08,
            high=0.18,
        )
    )

    df["heat_penalty"] = df["heat_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.06,
            high=0.15,
        )
    )

    df["wind_penalty"] = df["wind_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.04,
            high=0.10,
        )
    )

    df["air_quality_penalty"] = df["air_quality_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.05,
            high=0.12,
        )
    )

    df["uv_penalty"] = df["uv_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.04,
            high=0.10,
        )
    )

    df["visibility_penalty"] = df["visibility_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.04,
            high=0.10,
        )
    )

    df["overall_weather_penalty"] = df["weather_risk_level"].apply(
        lambda risk: risk_penalty(
            risk,
            medium=0.02,
            high=0.05,
        )
    )

    outdoor_factor = df["outdoor_weather_sensitive"].astype(bool).astype(float)

    df["weather_penalty"] = (
        outdoor_factor
        * (
            df["rain_penalty"]
            + df["heat_penalty"]
            + df["wind_penalty"]
            + df["air_quality_penalty"]
            + df["uv_penalty"]
            + df["visibility_penalty"]
        )
        + df["overall_weather_penalty"]
    )

    df["weather_penalty"] = df["weather_penalty"].clip(upper=0.35)

    df["final_score"] = (
        0.45 * df["rating_score"]
        + 0.35 * df["popularity_score"]
        + 0.20 * df["budget_score"]
        - df["news_penalty"]
        - df["weather_penalty"]
    )

    df["final_score"] = df["final_score"].clip(lower=0)

    return df.sort_values("final_score", ascending=False)