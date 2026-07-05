import pandas as pd

from src.scoring import score_places


def generate_itinerary(
    df: pd.DataFrame,
    city: str,
    days: int,
    budget_type: str,
    food_preference: str = "any",
    travel_style: str = "balanced",
) -> dict:
    city_df = df[df["city"].str.lower() == city.lower()].copy()
    scored = score_places(city_df, budget_type=budget_type)

    attractions = scored[scored["is_tourist_spot"] == True].copy()
    food = scored[scored["is_food"] == True].copy()

    # Keep food preference simple and explainable for MVP.
    if food_preference == "street food":
        food = food[food["source_query"].str.contains("street", case=False, na=False)]
    elif food_preference == "fine dining":
        food = food[food["source_query"].str.contains("fine|luxury", case=False, na=False)]

    if travel_style == "relaxed":
        spots_per_day = 2
    elif travel_style == "fast":
        spots_per_day = 4
    else:
        spots_per_day = 3

    itinerary = {}
    attraction_index = 0
    food_index = 0

    for day in range(1, days + 1):
        day_spots = attractions.iloc[attraction_index : attraction_index + spots_per_day]
        attraction_index += spots_per_day

        lunch = food.iloc[food_index % len(food)] if len(food) else None
        dinner = food.iloc[(food_index + 1) % len(food)] if len(food) > 1 else None
        food_index += 2

        itinerary[f"Day {day}"] = {
            "morning": day_spots.iloc[0].to_dict() if len(day_spots) > 0 else None,
            "afternoon": day_spots.iloc[1].to_dict() if len(day_spots) > 1 else None,
            "evening": day_spots.iloc[2].to_dict() if len(day_spots) > 2 else None,
            "lunch": lunch.to_dict() if lunch is not None else None,
            "dinner": dinner.to_dict() if dinner is not None else None,
        }

    return itinerary
