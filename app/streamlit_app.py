import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.itinerary import generate_itinerary
from src.scoring import score_places


st.set_page_config(
    page_title="TripSense AI",
    layout="wide",
)


def first_existing_path(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path

    return None


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def get_configured_cities() -> list[str]:
    value = os.getenv("TRIPSENSE_CITIES", "Jaipur,Mumbai")
    return [city.strip() for city in value.split(",") if city.strip()]


def normalize_city(value) -> str:
    return str(value).strip().lower()


def normalize_risk(value) -> str:
    value = str(value or "Low").strip().lower()

    if value == "high":
        return "High"

    if value == "medium":
        return "Medium"

    return "Low"


def to_bool(value) -> bool:
    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()
    return value in ["true", "1", "yes", "y"]


def get_value(row, candidates: list[str], default=""):
    for col in candidates:
        if col in row.index:
            value = row.get(col)
            if pd.notna(value):
                return value

    return default


def apply_weather_context_to_places(
    places: pd.DataFrame,
    selected_weather: pd.DataFrame,
) -> pd.DataFrame:
    places = places.copy()

    default_weather_values = {
        "weather_risk_level": "Low",
        "primary_weather_risk": "None",
        "rain_risk_level": "Low",
        "heat_risk_level": "Low",
        "wind_risk_level": "Low",
        "air_quality_risk_level": "Low",
        "uv_risk_level": "Low",
        "visibility_risk_level": "Low",
        "weather_lookahead_hours": 0,
        "rain_mm_next_window": 0,
        "max_rain_probability": 0,
        "max_temperature_c": 0,
        "max_wind_speed": 0,
        "air_quality_index": "",
        "max_uv_index": "",
        "min_visibility_km": "",
        "weather_travel_advice": "",
    }

    if selected_weather.empty:
        for col, value in default_weather_values.items():
            places[col] = value

        return places

    weather_row = selected_weather.iloc[0]

    places["weather_risk_level"] = normalize_risk(
        get_value(weather_row, ["weather_risk_level"], "Low")
    )
    places["primary_weather_risk"] = get_value(
        weather_row,
        ["primary_weather_risk"],
        "None",
    )
    places["rain_risk_level"] = normalize_risk(
        get_value(weather_row, ["rain_risk_level"], "Low")
    )
    places["heat_risk_level"] = normalize_risk(
        get_value(weather_row, ["heat_risk_level"], "Low")
    )
    places["wind_risk_level"] = normalize_risk(
        get_value(weather_row, ["wind_risk_level"], "Low")
    )
    places["air_quality_risk_level"] = normalize_risk(
        get_value(weather_row, ["air_quality_risk_level"], "Low")
    )
    places["uv_risk_level"] = normalize_risk(
        get_value(weather_row, ["uv_risk_level"], "Low")
    )
    places["visibility_risk_level"] = normalize_risk(
        get_value(weather_row, ["visibility_risk_level"], "Low")
    )

    places["weather_lookahead_hours"] = get_value(
        weather_row,
        ["lookahead_hours", "weather_lookahead_hours"],
        0,
    )
    places["rain_mm_next_window"] = get_value(
        weather_row,
        ["rain_mm_next_window", "total_rain_mm"],
        0,
    )
    places["max_rain_probability"] = get_value(
        weather_row,
        ["max_rain_probability", "rain_probability"],
        0,
    )
    places["max_temperature_c"] = get_value(
        weather_row,
        ["max_temperature_c", "max_temperature", "temperature_max_c"],
        0,
    )
    places["max_wind_speed"] = get_value(
        weather_row,
        ["max_wind_speed", "max_wind_speed_kmph", "max_wind_speed_kmh"],
        0,
    )
    places["air_quality_index"] = get_value(
        weather_row,
        ["air_quality_index", "aqi", "european_aqi", "us_aqi"],
        "",
    )
    places["max_uv_index"] = get_value(
        weather_row,
        ["max_uv_index", "uv_index", "uv_index_max"],
        "",
    )
    places["min_visibility_km"] = get_value(
        weather_row,
        ["min_visibility_km", "visibility_km", "min_visibility"],
        "",
    )
    places["weather_travel_advice"] = get_value(
        weather_row,
        ["travel_advice", "weather_travel_advice"],
        "",
    )

    return places


places_path = first_existing_path(
    [
        ROOT / "data" / "processed" / "all_cities_places_clean.csv",
        ROOT / "data" / "processed" / "tripsense_places_clean.csv",
        ROOT / "data" / "processed" / "jaipur_mumbai_places_clean.csv",
        ROOT / "data" / "processed" / "jaipur_places_clean.csv",
    ]
)

news_summary_path = first_existing_path(
    [
        ROOT / "data" / "processed" / "place_news_summary.csv",
        ROOT / "data" / "processed" / "all_cities_place_news_summary.csv",
        ROOT / "data" / "processed" / "city_place_news_summary.csv",
        ROOT / "data" / "processed" / "jaipur_place_news_summary.csv",
        ROOT / "data" / "processed" / "mumbai_place_news_summary.csv",
    ]
)

weather_summary_path = ROOT / "data" / "processed" / "city_weather_summary.csv"


st.title("TripSense AI")
st.subheader("Google Cloud + NVIDIA Accelerated Local Travel, Food, News & Advanced Weather Planner")

if places_path is None:
    st.error(
        "Processed places data not found. Run these commands first:\n\n"
        "`python scripts/ingest_places.py`\n\n"
        "`python scripts/clean_places.py`"
    )
    st.stop()

places_df = load_csv(str(places_path))

if "city" not in places_df.columns:
    st.error("The places CSV must contain a `city` column for the multi-city MVP.")
    st.stop()

available_cities = sorted(
    [city for city in places_df["city"].dropna().unique().tolist()]
)

configured_cities = get_configured_cities()

available_city_lookup = {
    normalize_city(city): city
    for city in available_cities
}

city_options = []

for city_name in configured_cities:
    key = normalize_city(city_name)

    if key in available_city_lookup:
        city_options.append(available_city_lookup[key])

if not city_options:
    city_options = available_cities

default_city_index = 0

for idx, city_name in enumerate(city_options):
    if normalize_city(city_name) == "mumbai":
        default_city_index = idx
        break


if news_summary_path and news_summary_path.exists():
    news_df = load_csv(str(news_summary_path))
else:
    news_df = pd.DataFrame()


if weather_summary_path.exists():
    weather_df = load_csv(str(weather_summary_path))
else:
    weather_df = pd.DataFrame()


with st.sidebar:
    st.header("Trip Preferences")

    city = st.selectbox(
        "City",
        city_options,
        index=default_city_index,
    )

    days = st.slider(
        "Number of days",
        min_value=1,
        max_value=5,
        value=2,
    )

    budget_type = st.selectbox(
        "Budget type",
        ["budget", "standard", "luxury"],
    )

    food_preference = st.selectbox(
        "Food preference",
        ["any", "veg", "non-veg", "street food", "fine dining"],
    )

    travel_style = st.selectbox(
        "Travel style",
        ["relaxed", "balanced", "fast"],
    )


city_places_df = places_df[
    places_df["city"].apply(normalize_city) == normalize_city(city)
].copy()

if city_places_df.empty:
    st.error(f"No places found for {city}. Check your processed places CSV.")
    st.stop()


NEWS_DEFAULTS = {
    "news_count": 0,
    "incident_count": 0,
    "positive_count": 0,
    "news_risk_level": "Low",
    "news_signal_score": 0,
    "latest_article_title": "",
    "latest_article_url": "",
}


def add_news_defaults(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col, default_value in NEWS_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default_value

    df["news_count"] = df["news_count"].fillna(0).astype(int)
    df["incident_count"] = df["incident_count"].fillna(0).astype(int)
    df["positive_count"] = df["positive_count"].fillna(0).astype(int)
    df["news_signal_score"] = df["news_signal_score"].fillna(0).astype(int)
    df["news_risk_level"] = df["news_risk_level"].fillna("Low").apply(normalize_risk)
    df["latest_article_title"] = df["latest_article_title"].fillna("")
    df["latest_article_url"] = df["latest_article_url"].fillna("")

    return df


if not news_df.empty and "place_id" in news_df.columns:
    news_df = news_df.copy()

    if "city" in news_df.columns:
        news_df = news_df[
            news_df["city"].apply(normalize_city) == normalize_city(city)
        ].copy()

    news_columns = [
        "place_id",
        "news_count",
        "incident_count",
        "positive_count",
        "news_risk_level",
        "news_signal_score",
        "latest_article_title",
        "latest_article_url",
    ]

    available_news_columns = [
        col for col in news_columns
        if col in news_df.columns
    ]

    city_places_df = city_places_df.merge(
        news_df[available_news_columns].drop_duplicates(subset=["place_id"]),
        on="place_id",
        how="left",
    )

city_places_df = add_news_defaults(city_places_df)


selected_weather = pd.DataFrame()

if not weather_df.empty and "city" in weather_df.columns:
    selected_weather = weather_df[
        weather_df["city"].apply(normalize_city) == normalize_city(city)
    ].copy()


city_places_df = apply_weather_context_to_places(
    places=city_places_df,
    selected_weather=selected_weather,
)


st.markdown("## Live Context")

if selected_weather.empty:
    st.info(
        "Advanced weather risk data not found. Run: "
        "`python scripts/ingest_weather.py`"
    )
    selected_weather_risk = "Low"
else:
    weather_row = selected_weather.iloc[0]

    selected_weather_risk = normalize_risk(
        get_value(weather_row, ["weather_risk_level"], "Low")
    )

    primary_weather_risk = get_value(
        weather_row,
        ["primary_weather_risk"],
        "None",
    )

    travel_advice = str(
        get_value(
            weather_row,
            ["travel_advice", "weather_travel_advice"],
            "No weather advice available.",
        )
    )

    rain_mm = get_value(weather_row, ["rain_mm_next_window", "total_rain_mm"], 0)
    rain_prob = get_value(weather_row, ["max_rain_probability", "rain_probability"], 0)
    max_temp = get_value(weather_row, ["max_temperature_c", "max_temperature"], 0)
    wind_speed = get_value(weather_row, ["max_wind_speed", "max_wind_speed_kmph"], 0)
    aqi = get_value(weather_row, ["air_quality_index", "aqi", "european_aqi", "us_aqi"], "N/A")
    uv_index = get_value(weather_row, ["max_uv_index", "uv_index", "uv_index_max"], "N/A")
    visibility = get_value(weather_row, ["min_visibility_km", "visibility_km", "min_visibility"], "N/A")

    if selected_weather_risk == "High":
        st.error(
            f"Weather Risk: {selected_weather_risk} — "
            f"Primary issue: {primary_weather_risk}. {travel_advice}"
        )
    elif selected_weather_risk == "Medium":
        st.warning(
            f"Weather Risk: {selected_weather_risk} — "
            f"Primary issue: {primary_weather_risk}. {travel_advice}"
        )
    else:
        st.success(
            f"Weather Risk: {selected_weather_risk} — "
            f"Primary issue: {primary_weather_risk}. {travel_advice}"
        )

    metric_cols = st.columns(6)

    with metric_cols[0]:
        st.metric("Rain", f"{rain_mm} mm")

    with metric_cols[1]:
        st.metric("Rain probability", f"{rain_prob}%")

    with metric_cols[2]:
        st.metric("Max temp", f"{max_temp} °C")

    with metric_cols[3]:
        st.metric("Wind", f"{wind_speed}")

    with metric_cols[4]:
        st.metric("AQI", f"{aqi}")

    with metric_cols[5]:
        st.metric("UV / visibility", f"{uv_index} / {visibility}")

    risk_cols = st.columns(5)

    with risk_cols[0]:
        st.write(f"Rain risk: **{normalize_risk(get_value(weather_row, ['rain_risk_level'], 'Low'))}**")

    with risk_cols[1]:
        st.write(f"Heat risk: **{normalize_risk(get_value(weather_row, ['heat_risk_level'], 'Low'))}**")

    with risk_cols[2]:
        st.write(f"Wind risk: **{normalize_risk(get_value(weather_row, ['wind_risk_level'], 'Low'))}**")

    with risk_cols[3]:
        st.write(f"Air quality risk: **{normalize_risk(get_value(weather_row, ['air_quality_risk_level'], 'Low'))}**")

    with risk_cols[4]:
        st.write(
            f"UV / visibility risk: "
            f"**{normalize_risk(get_value(weather_row, ['uv_risk_level'], 'Low'))} / "
            f"{normalize_risk(get_value(weather_row, ['visibility_risk_level'], 'Low'))}**"
        )

    if selected_weather_risk in ["High", "Medium"]:
        st.info(
            "TripSense AI adjusted the ranking using advanced city-level weather context. "
            "Outdoor places get stronger penalties for rain, heat, wind, poor air quality, high UV, or low visibility."
        )


def render_news_badge(place: dict) -> None:
    risk = normalize_risk(place.get("news_risk_level", "Low"))
    news_count = int(place.get("news_count", 0) or 0)
    incident_count = int(place.get("incident_count", 0) or 0)
    latest_title = str(place.get("latest_article_title", "") or "")
    latest_url = str(place.get("latest_article_url", "") or "")

    if news_count == 0:
        st.caption("News signal: Low — no recent place-specific match")
        return

    message = (
        f"News signal: {risk} | "
        f"Articles: {news_count} | "
        f"Incident signals: {incident_count}"
    )

    if risk == "High":
        st.error(message)
    elif risk == "Medium":
        st.warning(message)
    else:
        st.success(message)

    if latest_title and latest_url:
        st.markdown(f"[Latest related article]({latest_url})")
    elif latest_title:
        st.caption(f"Latest: {latest_title}")


def render_weather_badge(place: dict) -> None:
    weather_risk = normalize_risk(place.get("weather_risk_level", "Low"))
    outdoor_sensitive = to_bool(place.get("outdoor_weather_sensitive", False))
    weather_penalty = float(place.get("weather_penalty", 0) or 0)

    primary_risk = place.get("primary_weather_risk", "None")

    sub_risks = {
        "Rain": normalize_risk(place.get("rain_risk_level", "Low")),
        "Heat": normalize_risk(place.get("heat_risk_level", "Low")),
        "Wind": normalize_risk(place.get("wind_risk_level", "Low")),
        "AQI": normalize_risk(place.get("air_quality_risk_level", "Low")),
        "UV": normalize_risk(place.get("uv_risk_level", "Low")),
        "Visibility": normalize_risk(place.get("visibility_risk_level", "Low")),
    }

    active_risks = [
        f"{name}: {risk}"
        for name, risk in sub_risks.items()
        if risk in ["Medium", "High"]
    ]

    if weather_risk == "High" and outdoor_sensitive:
        st.warning(
            f"Weather-sensitive place. Primary risk: {primary_risk}. "
            f"Penalty applied: {weather_penalty:.2f}"
        )
    elif weather_risk == "Medium" and outdoor_sensitive:
        st.warning(
            f"Weather-sensitive place. Primary risk: {primary_risk}. "
            f"Penalty applied: {weather_penalty:.2f}"
        )
    elif weather_risk in ["High", "Medium"]:
        st.caption(
            f"City-wide weather caution active. Penalty: {weather_penalty:.2f}"
        )

    if active_risks:
        st.caption("Weather factors: " + ", ".join(active_risks))


def render_place_card(slot: str, place: dict) -> None:
    st.markdown(f"**{slot.title()}**")

    if not place:
        st.write("No recommendation available")
        return

    place_name = place.get("name", "Unknown place")
    maps_url = place.get("google_maps_uri", "")
    score = float(place.get("final_score", 0) or 0)

    if maps_url:
        st.markdown(f"[{place_name}]({maps_url})")
    else:
        st.markdown(place_name)

    st.write(f"Rating: {place.get('rating', 'N/A')}")
    st.write(f"Reviews: {place.get('user_rating_count', 'N/A')}")
    st.write(f"Type: {place.get('primary_type', 'N/A')}")
    st.write(f"Score: {score:.2f}")

    render_news_badge(place)
    render_weather_badge(place)


st.markdown("## Itinerary Generator")

if st.button("Generate itinerary"):
    itinerary = generate_itinerary(
        df=city_places_df,
        city=city,
        days=days,
        budget_type=budget_type,
        food_preference=food_preference,
        travel_style=travel_style,
    )

    st.header("Recommended itinerary")

    for day, plan in itinerary.items():
        st.markdown(f"### {day}")

        cols = st.columns(5)

        for idx, (slot, place) in enumerate(plan.items()):
            with cols[idx % 5]:
                render_place_card(
                    slot=slot,
                    place=place,
                )


st.header("Top ranked places")

scored_df = score_places(
    city_places_df,
    budget_type=budget_type,
)

display_columns = [
    "name",
    "city",
    "query_category",
    "rating",
    "user_rating_count",
    "price_level",
    "news_risk_level",
    "news_count",
    "incident_count",
    "weather_risk_level",
    "primary_weather_risk",
    "rain_risk_level",
    "heat_risk_level",
    "wind_risk_level",
    "air_quality_risk_level",
    "uv_risk_level",
    "visibility_risk_level",
    "rain_mm_next_window",
    "max_rain_probability",
    "max_temperature_c",
    "air_quality_index",
    "max_uv_index",
    "min_visibility_km",
    "outdoor_weather_sensitive",
    "news_penalty",
    "weather_penalty",
    "final_score",
]

available_display_columns = [
    col for col in display_columns
    if col in scored_df.columns
]

st.dataframe(
    scored_df[available_display_columns].head(30),
    use_container_width=True,
)


with st.expander("Data status"):
    st.write(f"Places file: `{places_path}`")
    st.write(f"Places rows for {city}: {len(city_places_df)}")

    if news_summary_path:
        st.write(f"News summary file: `{news_summary_path}`")
    else:
        st.write("News summary file: not found")

    if weather_summary_path.exists():
        st.write(f"Weather summary file: `{weather_summary_path}`")
    else:
        st.write("Weather summary file: not found")

    st.write("Available cities:", available_cities)

    if not selected_weather.empty:
        st.write("Selected city weather row:")
        st.dataframe(selected_weather, use_container_width=True)
    else:
        st.write("No selected city weather row")