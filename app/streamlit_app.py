import sys
from pathlib import Path
import pandas as pd
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.itinerary import generate_itinerary
from src.scoring import score_places
st.set_page_config(page_title="TripSense AI", layout="wide")
st.title("TripSense AI")
st.subheader("Google Cloud + NVIDIA Accelerated Local Travel & Food Planner")
csv_path = ROOT / "data" / "processed" / "jaipur_places_clean.csv"
if not csv_path.exists():
    st.error(
        "Processed data not found. Run: "
        "`python scripts/ingest_places.py` and `python scripts/clean_places.py` first."
    )
    st.stop()
df = pd.read_csv(csv_path)
with st.sidebar:
    st.header("Trip Preferences")
    city = st.selectbox("City", ["Jaipur"])
    days = st.slider("Number of days", min_value=1, max_value=5, value=2)
    budget_type = st.selectbox("Budget type", ["budget", "standard", "luxury"])
    food_preference = st.selectbox(
        "Food preference",
        ["any", "veg", "non-veg", "street food", "fine dining"],
    )
    travel_style = st.selectbox("Travel style", ["relaxed", "balanced", "fast"])
if st.button("Generate itinerary"):
    itinerary = generate_itinerary(
        df=df,
        days=days,
        budget_type=budget_type,
        food_preference=food_preference,
        travel_style=travel_style,
    )
    st.header("Recommended itinerary")
    for day, plan in itinerary.items():
        st.markdown(f"## {day}")
        cols = st.columns(5)
        for idx, (slot, place) in enumerate(plan.items()):
            with cols[idx % 5]:
                if place:
                    maps_url = place.get("google_maps_uri", "")
                    score = place.get("final_score", 0)
                    st.markdown(f"**{slot.title()}**")
                    st.markdown(f"[{place['name']}]({maps_url})")
                    st.write(f"Rating: {place['rating']}")
                    st.write(f"Reviews: {place['user_rating_count']}")
                    st.write(f"Type: {place.get('primary_type', 'N/A')}")
                    st.write(f"Score: {score:.2f}")
                else:
                    st.markdown(f"**{slot.title()}**")
                    st.write("No recommendation available")
    st.header("Top ranked places")
    scored_df = score_places(df, budget_type=budget_type)
    st.dataframe(
        scored_df[
            [
                "name",
                "query_category",
                "rating",
                "user_rating_count",
                "price_level",
                "final_score",
            ]
        ].head(30),
        use_container_width=True,
    )