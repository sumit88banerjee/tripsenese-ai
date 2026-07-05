-- Recreate this after loading places, place_news_summary, and city_weather_summary.
CREATE OR REPLACE TABLE `tripsense-ai.tripsense_ai.place_dashboard` AS
SELECT
  p.place_id,
  p.name,
  p.city,
  p.query_category,
  p.primary_type,
  p.rating,
  p.user_rating_count,
  p.price_level,
  p.latitude,
  p.longitude,
  p.google_maps_uri,
  IFNULL(n.news_count, 0) AS news_count,
  IFNULL(n.incident_count, 0) AS incident_count,
  IFNULL(n.positive_count, 0) AS positive_count,
  IFNULL(n.news_risk_level, 'Low') AS news_risk_level,
  IFNULL(n.news_signal_score, 0) AS news_signal_score,
  IFNULL(w.weather_risk_level, 'Low') AS weather_risk_level,
  IFNULL(w.primary_weather_risk, 'None') AS primary_weather_risk,
  IFNULL(w.rain_risk_level, 'Low') AS rain_risk_level,
  IFNULL(w.heat_risk_level, 'Low') AS heat_risk_level,
  IFNULL(w.wind_risk_level, 'Low') AS wind_risk_level,
  IFNULL(w.air_quality_risk_level, 'Low') AS air_quality_risk_level,
  IFNULL(w.uv_risk_level, 'Low') AS uv_risk_level,
  IFNULL(w.visibility_risk_level, 'Low') AS visibility_risk_level,
  IFNULL(w.rain_mm_next_window, 0) AS rain_mm_next_window,
  IFNULL(w.max_rain_probability, 0) AS max_rain_probability,
  IFNULL(w.max_apparent_temperature_c, 0) AS max_apparent_temperature_c,
  IFNULL(w.max_wind_gust_kmph, 0) AS max_wind_gust_kmph,
  IFNULL(w.max_us_aqi, 0) AS max_us_aqi,
  IFNULL(w.max_pm25, 0) AS max_pm25,
  IFNULL(w.max_uv_index, 0) AS max_uv_index,
  IFNULL(w.min_visibility_m, 99999) AS min_visibility_m,
  IFNULL(w.travel_advice, '') AS weather_travel_advice,
  CASE
    WHEN p.query_category = 'food' THEN 'Food'
    WHEN p.query_category = 'tourist_spot' THEN 'Tourist Spot'
    ELSE 'Other'
  END AS place_group,
  CASE
    WHEN LOWER(p.name) LIKE '%beach%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%marine drive%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%chowpatty%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%fort%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%bazaar%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%market%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%garden%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%lake%' THEN TRUE
    WHEN LOWER(p.name) LIKE '%ghat%' THEN TRUE
    WHEN LOWER(p.primary_type) LIKE '%park%' THEN TRUE
    WHEN p.query_category = 'tourist_spot' THEN TRUE
    ELSE FALSE
  END AS outdoor_weather_sensitive
FROM `tripsense-ai.tripsense_ai.places` p
LEFT JOIN `tripsense-ai.tripsense_ai.place_news_summary` n
USING (place_id)
LEFT JOIN `tripsense-ai.tripsense_ai.city_weather_summary` w
ON LOWER(p.city) = LOWER(w.city);

CREATE OR REPLACE TABLE `tripsense-ai.tripsense_ai.top_places_news_weather_aware` AS
SELECT
  *,
  rating * LOG(user_rating_count + 1) AS simple_popularity_score,
  CASE
    WHEN news_risk_level = 'High' THEN 0.15
    WHEN news_risk_level = 'Medium' THEN 0.08
    ELSE 0
  END AS news_penalty,
  CASE
    WHEN weather_risk_level = 'High' AND outdoor_weather_sensitive = TRUE THEN 0.22
    WHEN weather_risk_level = 'Medium' AND outdoor_weather_sensitive = TRUE THEN 0.12
    WHEN weather_risk_level = 'High' THEN 0.06
    WHEN weather_risk_level = 'Medium' THEN 0.03
    ELSE 0
  END AS weather_penalty,
  (
    rating * LOG(user_rating_count + 1)
    - CASE
        WHEN news_risk_level = 'High' THEN 0.15
        WHEN news_risk_level = 'Medium' THEN 0.08
        ELSE 0
      END
    - CASE
        WHEN weather_risk_level = 'High' AND outdoor_weather_sensitive = TRUE THEN 0.22
        WHEN weather_risk_level = 'Medium' AND outdoor_weather_sensitive = TRUE THEN 0.12
        WHEN weather_risk_level = 'High' THEN 0.06
        WHEN weather_risk_level = 'Medium' THEN 0.03
        ELSE 0
      END
  ) AS news_weather_adjusted_score
FROM `tripsense-ai.tripsense_ai.place_dashboard`
ORDER BY news_weather_adjusted_score DESC;