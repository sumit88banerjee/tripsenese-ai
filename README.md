# TripSense AI

TripSense AI is a multi-city travel and food itinerary planner that combines Google Cloud data pipelines, GDELT news intelligence, advanced weather risk analysis, and NVIDIA RAPIDS acceleration benchmarking.

The app recommends day-wise tourist places and food options for Indian cities while considering:

- Google Places rating and popularity
- Budget or luxury preference
- Food preference
- Travel style
- Recent news and incident signals from GDELT
- Advanced city-level weather risks:
  - Heavy rain
  - Heat
  - Wind / storm
  - Air quality
  - UV index
  - Visibility
- Outdoor-place sensitivity
- NVIDIA cuDF acceleration benchmark for faster scoring and re-ranking

Current MVP cities:

```text
Jaipur
Mumbai
```

---

## Problem Statement

Tourists usually rely only on ratings when choosing where to visit or eat. But ratings alone do not answer important real-world questions:

```text
Is this place safe today?
Is there heavy rain in the city?
Is it too hot for outdoor sightseeing?
Is air quality bad?
Is UV high?
Is visibility poor?
Was there any recent news or incident around this place?
Should outdoor places be avoided today?
```

TripSense AI solves this by combining static place intelligence with live context signals.

---

## Key Features

### 1. Multi-city itinerary planner

Supports multiple cities through the environment variable:

```env
TRIPSENSE_CITIES=Jaipur,Mumbai
```

The current MVP supports Jaipur and Mumbai.

---

### 2. Google Places ingestion

TripSense AI uses Google Places API to collect:

- Tourist places
- Historical places
- Shopping markets
- Local food restaurants
- Street food
- Luxury restaurants

Raw API output is saved under:

```text
data/raw/
```

Cleaned multi-city data is saved as:

```text
data/processed/all_cities_places_clean.csv
```

---

### 3. GDELT news intelligence

TripSense AI uses public GDELT DOC API calls to detect recent news and incident signals.

GDELT is used for:

- Local incidents
- Viral news
- Safety concerns
- Crowd issues
- Closures
- Protests
- Scams
- Weather-related disruption news
- Positive tourism news

GDELT does not require an API key for the public DOC API used in this MVP.

Processed outputs:

```text
data/processed/place_news.csv
data/processed/place_news_summary.csv
```

---

### 4. Advanced weather risk intelligence

TripSense AI uses weather and air-quality data to detect city-wide travel risk.

The current weather model checks:

```text
Rain risk
Heat risk
Wind / storm risk
Air quality risk
UV risk
Visibility risk
```

This is important because city-wide risks may not mention a specific tourist place.

Example:

```text
Mumbai heavy rain may not mention Gateway of India or Marine Drive directly,
but the itinerary should still warn the user and reduce outdoor recommendations.
```

Processed output:

```text
data/processed/city_weather_summary.csv
```

---

### 5. News + weather-aware scoring

The scoring engine combines:

```text
rating_score
popularity_score
budget_score
news_penalty
weather_penalty
```

Final scoring formula:

```text
final_score =
  0.45 * rating_score
+ 0.35 * popularity_score
+ 0.20 * budget_score
- news_penalty
- weather_penalty
```

Weather penalties are stronger for outdoor/weather-sensitive places such as:

```text
beaches
forts
markets
gardens
lakes
ghats
waterfronts
monuments
outdoor tourist spots
```

---

### 6. Streamlit app

The Streamlit app provides:

- City selector
- Number of days
- Budget type
- Food preference
- Travel style
- Live context section
- Weather risk banner
- News signal badges
- Weather-sensitive place warnings
- Ranked places table
- Day-wise itinerary

Run locally:

```bash
streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0
```

For Google Cloud Shell preview:

```bash
streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false
```

---

### 7. Google Cloud integration

TripSense AI uses Google Cloud for:

```text
Cloud Storage
BigQuery
Cloud Run
Looker Studio
Cloud Build
Artifact Registry
```

Cloud Storage is used for:

```text
raw Places API JSON
raw GDELT JSON
raw weather JSON
processed CSV files
```

BigQuery is used for:

```text
analytics tables
dashboard tables
Looker Studio reports
news/weather-aware ranking tables
```

Cloud Run is used to deploy the Streamlit app.

---

### 8. NVIDIA acceleration layer

TripSense AI includes a benchmark using:

```text
pandas CPU
cuDF / cudf.pandas GPU
```

This demonstrates how itinerary scoring and re-ranking can be accelerated when the dataset scales.

CPU benchmark:

```bash
python scripts/run_benchmark_cpu.py
```

GPU benchmark:

```bash
python scripts/run_benchmark_gpu.py
```

Install GPU dependencies only in a GPU runtime:

```bash
pip install -r requirements-gpu.txt
```

---

## Project Structure

```text
tripsense-ai/
│
├── app/
│   └── streamlit_app.py
│
├── src/
│   ├── places_api.py
│   ├── data_cleaning.py
│   ├── news_intelligence.py
│   ├── weather_intelligence.py
│   ├── scoring.py
│   ├── itinerary.py
│   ├── bigquery_io.py
│   └── benchmark.py
│
├── scripts/
│   ├── ingest_places.py
│   ├── clean_places.py
│   ├── ingest_news.py
│   ├── ingest_weather.py
│   ├── load_to_bigquery.py
│   ├── load_news_to_bigquery.py
│   ├── run_benchmark_cpu.py
│   └── run_benchmark_gpu.py
│
├── sql/
│   └── weather_dashboard_tables.sql
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── config/
│       └── place_aliases.csv
│
├── docs/
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── requirements.txt
├── requirements-gpu.txt
└── README.md
```

---

## Environment Setup

Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## `.env.example`

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Example:

```env
# Google Places API
GOOGLE_MAPS_API_KEY=your_places_api_key

# Google Cloud
GOOGLE_CLOUD_PROJECT=your_project_id
GCS_BUCKET=your_bucket_name
BIGQUERY_DATASET=tripsense_ai

# Multi-city MVP
TRIPSENSE_CITIES=Jaipur,Mumbai
PLACES_MAX_RESULTS=20

# GDELT / News Intelligence
NEWS_LOOKBACK_DAYS=90
GDELT_MAX_RECORDS=100
NEWS_TOP_N_PLACES=40
NEWS_CACHE_HOURS=24
GDELT_MAX_RETRIES=5

# Advanced weather risk
ENABLE_WEATHER_RISK=true
WEATHER_LOOKAHEAD_HOURS=12
WEATHER_CACHE_HOURS=3

# Rain thresholds
RAIN_MM_12H_MEDIUM=10
RAIN_MM_12H_HIGH=30
RAIN_PROB_MEDIUM=60
RAIN_PROB_HIGH=80

# Heat thresholds
TEMP_C_MEDIUM=35
TEMP_C_HIGH=40

# Wind thresholds
WIND_KMPH_MEDIUM=35
WIND_KMPH_HIGH=50

# Air quality thresholds
AQI_MEDIUM=100
AQI_HIGH=150

# UV thresholds
UV_MEDIUM=6
UV_HIGH=8

# Visibility thresholds
VISIBILITY_KM_MEDIUM=5
VISIBILITY_KM_HIGH=2
```

Do not commit `.env`.

---

## Local Pipeline Run

Run the full pipeline:

```bash
python scripts/ingest_places.py
python scripts/clean_places.py
python scripts/ingest_news.py
python scripts/ingest_weather.py
```

Expected processed files:

```text
data/processed/all_cities_places_clean.csv
data/processed/place_news.csv
data/processed/place_news_summary.csv
data/processed/city_weather_summary.csv
```

Verify cities:

```bash
python - <<'PY'
import pandas as pd

df = pd.read_csv("data/processed/all_cities_places_clean.csv")
print(df["city"].value_counts())
PY
```

Expected:

```text
Jaipur
Mumbai
```

---

## Run Streamlit Locally

```bash
streamlit cache clear

streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0
```

For Cloud Shell:

```bash
streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false
```

---

## Google Cloud Setup

Set variables:

```bash
export PROJECT_ID="tripsense-ai-sumit-2026"
export REGION="asia-south1"
export BUCKET_NAME="${PROJECT_ID}-data"

gcloud config set project $PROJECT_ID
```

Enable required APIs:

```bash
gcloud services enable \
  places.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com
```

Create Cloud Storage bucket:

```bash
gcloud storage buckets create gs://$BUCKET_NAME \
  --location=$REGION \
  --uniform-bucket-level-access
```

Create BigQuery dataset:

```bash
bq --location=$REGION mk --dataset $PROJECT_ID:tripsense_ai
```

---

## Upload Data to Cloud Storage

```bash
gcloud storage cp -r data/raw gs://$BUCKET_NAME/
gcloud storage cp -r data/processed gs://$BUCKET_NAME/
```

---

## Load Data into BigQuery

Load places:

```bash
bq load \
  --replace \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  $PROJECT_ID:tripsense_ai.places \
  data/processed/all_cities_places_clean.csv
```

Load news:

```bash
bq load \
  --replace \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  $PROJECT_ID:tripsense_ai.place_news \
  data/processed/place_news.csv
```

Load news summary:

```bash
bq load \
  --replace \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  $PROJECT_ID:tripsense_ai.place_news_summary \
  data/processed/place_news_summary.csv
```

Load weather summary:

```bash
bq load \
  --replace \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  $PROJECT_ID:tripsense_ai.city_weather_summary \
  data/processed/city_weather_summary.csv
```

Create dashboard tables:

```bash
bq query --use_legacy_sql=false < sql/weather_dashboard_tables.sql
```

---

## BigQuery Dashboard Tables

The SQL file:

```text
sql/weather_dashboard_tables.sql
```

is used to create dashboard-ready BigQuery tables.

It joins:

```text
places
place_news_summary
city_weather_summary
```

and creates tables such as:

```text
place_dashboard
top_places_news_weather_aware
```

Use these tables in Looker Studio for:

- Top places by city
- News risk by place
- Weather risk by city
- Outdoor-sensitive places
- News/weather-adjusted ranking
- Rating vs review count
- Budget vs luxury analysis

---

## Local Streamlit vs BigQuery

Current Streamlit app reads local CSV files:

```text
data/processed/all_cities_places_clean.csv
data/processed/place_news_summary.csv
data/processed/city_weather_summary.csv
```

BigQuery is used for:

```text
analytics
dashboarding
Looker Studio
cloud architecture proof
```

This means:

```text
Local app = CSV snapshot
Dashboard = BigQuery tables
```

To make the app always use the latest cloud data, the app can later be upgraded to read from:

```text
tripsense_ai.top_places_news_weather_aware
```

---

## Cloud Run Deployment

Make sure processed CSV files exist before deploying:

```bash
ls -lh data/processed
```

Expected:

```text
all_cities_places_clean.csv
place_news_summary.csv
city_weather_summary.csv
```

Create Cloud Run env file:

```bash
cat > cloudrun.env.yaml <<EOF
GOOGLE_CLOUD_PROJECT: "$PROJECT_ID"
GCS_BUCKET: "$BUCKET_NAME"
BIGQUERY_DATASET: "tripsense_ai"
TRIPSENSE_CITIES: "Jaipur,Mumbai"
WEATHER_LOOKAHEAD_HOURS: "12"
NEWS_LOOKBACK_DAYS: "90"
EOF
```

Deploy:

```bash
gcloud run deploy tripsense-ai \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --env-vars-file cloudrun.env.yaml
```

---

## Dockerfile

The app uses Streamlit on port `8080`.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

---

## `.dockerignore`

Because the deployed Streamlit app reads processed CSV files, do not ignore `data/processed`.

Recommended:

```dockerignore
.venv/
.env
__pycache__/
*.pyc
.git/
.gitignore

data/raw/

*.log
.DS_Store
```

---

## Demo Story

TripSense AI helps a tourist plan a Mumbai or Jaipur trip.

Instead of only showing popular places, it checks:

```text
Is the place highly rated?
Is it popular?
Does it match the user's budget?
Is there recent negative news?
Is there a city-wide weather risk?
Is the place outdoor-sensitive?
Should the user avoid it today?
```

Example:

```text
Mumbai has high rain risk.
TripSense AI warns the user.
Outdoor places like beaches and seafront walks receive a weather penalty.
Indoor restaurants, museums, and malls become safer recommendations.
```

Example:

```text
Jaipur has heat risk.
TripSense AI suggests avoiding heavy outdoor sightseeing in the afternoon.
It recommends a more comfortable itinerary.
```

---

## Hackathon Architecture

```text
Google Places API
        ↓
Cloud Storage raw JSON
        ↓
Python cleaning pipeline
        ↓
BigQuery places table
        ↓
GDELT news intelligence
        ↓
BigQuery place_news_summary
        ↓
Open-Meteo weather + air quality
        ↓
BigQuery city_weather_summary
        ↓
News + weather-aware scoring
        ↓
Streamlit app on Cloud Run
        ↓
Looker Studio dashboard
        ↓
NVIDIA RAPIDS cuDF benchmark
```

---

## Commands Summary

Full local rebuild:

```bash
python scripts/ingest_places.py
python scripts/clean_places.py
python scripts/ingest_news.py
python scripts/ingest_weather.py
```

Run app:

```bash
streamlit cache clear

streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0
```

Upload to GCS:

```bash
gcloud storage cp -r data/raw gs://$BUCKET_NAME/
gcloud storage cp -r data/processed gs://$BUCKET_NAME/
```

Load BigQuery:

```bash
bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.places \
  data/processed/all_cities_places_clean.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.place_news \
  data/processed/place_news.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.place_news_summary \
  data/processed/place_news_summary.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.city_weather_summary \
  data/processed/city_weather_summary.csv
```

Run dashboard SQL:

```bash
bq query --use_legacy_sql=false < sql/weather_dashboard_tables.sql
```

Deploy Cloud Run:

```bash
gcloud run deploy tripsense-ai \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --env-vars-file cloudrun.env.yaml
```

---

## Troubleshooting

### Streamlit only shows Jaipur

Check if Mumbai exists in the processed CSV:

```bash
python - <<'PY'
import pandas as pd

df = pd.read_csv("data/processed/all_cities_places_clean.csv")
print(df["city"].value_counts())
PY
```

If Mumbai is missing, rerun:

```bash
python scripts/ingest_places.py
python scripts/clean_places.py
```

---

### `clean_places.py` cannot find `all_cities_places_raw.json`

Check raw files:

```bash
ls -lh data/raw
```

If you have:

```text
data/raw/all_places_raw.json
```

but not:

```text
data/raw/all_cities_places_raw.json
```

copy it:

```bash
cp data/raw/all_places_raw.json data/raw/all_cities_places_raw.json
python scripts/clean_places.py
```

---

### GDELT returns 429 Too Many Requests

Reduce request volume or use cache:

```env
NEWS_CACHE_HOURS=24
GDELT_MAX_RECORDS=50
```

Then rerun:

```bash
python scripts/ingest_news.py
```

---

### Mumbai heavy rain not shown

Rerun weather ingestion:

```bash
python scripts/ingest_weather.py
```

Check:

```bash
cat data/processed/city_weather_summary.csv
```

---

### Cloud Run deploy env var error with `Jaipur,Mumbai`

Use env vars file instead of inline comma-separated env vars:

```bash
gcloud run deploy tripsense-ai \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --env-vars-file cloudrun.env.yaml
```

---

## Git Commit

Check changes:

```bash
git status
```

Add source and required processed snapshot files:

```bash
git add \
  README.md \
  app/streamlit_app.py \
  src/ \
  scripts/ \
  sql/ \
  Dockerfile \
  .dockerignore \
  .gitignore \
  .env.example \
  requirements.txt \
  requirements-gpu.txt \
  data/config/ \
  data/processed/
```

Commit:

```bash
git commit -m "Add multi-city news and advanced weather-aware itinerary scoring"
```

Push:

```bash
git push origin $(git branch --show-current)
```

Do not commit:

```text
.env
.venv/
data/raw/
__pycache__/
```

---

## Final Submission Notes

For the hackathon, explain:

```text
TripSense AI is not just a travel recommender.
It is a decision-support system that combines place quality, popularity, budget, local news, weather risk, and GPU-accelerated scoring evidence.
```

Key judging points:

```text
Real-world user problem
Data ingestion pipeline
Google Cloud storage and analytics
BigQuery dashboard layer
News intelligence
Advanced weather risk model
NVIDIA RAPIDS acceleration benchmark
Streamlit app deployed on Cloud Run
```
