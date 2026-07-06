# TripSense AI

**Live-context travel decision-support app for Jaipur + Mumbai**  
**Google Cloud + BigQuery + Cloud Storage + GDELT + Open-Meteo + NVIDIA RAPIDS**

TripSense AI is a prototype MVP that helps travellers decide **where it is sensible to go today**, not only which places are popular. It combines place popularity, budget fit, recent news/disruption signals, weather risk, air quality, UV risk, and visibility risk into a ranked travel recommendation dashboard.

The current MVP supports two Indian cities:

- Jaipur
- Mumbai

The project is designed for hackathon/demo submission and includes an NVIDIA acceleration layer using **RAPIDS cuDF / cudf.pandas** for GPU-accelerated tabular ranking and benchmarking.

---

## 1. Problem Statement

Travellers usually rely on rating-based recommendations, but ratings alone do not answer important real-time questions:

- Is it too hot for outdoor sightseeing?
- Is heavy rain or flooding likely?
- Is air quality poor?
- Is UV exposure high?
- Is visibility poor for viewpoints or long drives?
- Are there recent news incidents, disruptions, closures, or viral issues around a place?

TripSense AI solves this by adding a **Live Context Layer** on top of normal place ranking.

---

## 2. MVP Features

### Core features

- Multi-city support for Jaipur and Mumbai
- Google Places ingestion
- Data cleaning into a unified processed CSV
- GDELT news and disruption intelligence
- Open-Meteo weather forecast intelligence
- Open-Meteo air-quality intelligence
- Weather risk scoring across:
  - Rain
  - Heat
  - Wind / storm
  - Air quality
  - UV index
  - Visibility
- Outdoor-sensitive place detection
- Weather-aware ranking penalty
- News-aware ranking penalty
- Streamlit dashboard
- BigQuery dashboard tables
- NVIDIA RAPIDS GPU ranking layer
- CPU vs GPU benchmark evidence

---

## 3. Architecture

```text
Google Places API
        ↓
data/raw/*_places_raw.json
        ↓
data/processed/all_cities_places_clean.csv
        ↓
Cloud Storage + BigQuery tripsense_ai.places
```

```text
GDELT DOC 2.0 API
        ↓
data/processed/place_news_summary.csv
        ↓
Cloud Storage + BigQuery tripsense_ai.place_news_summary
```

```text
Open-Meteo Forecast API
Open-Meteo Air Quality API
        ↓
data/raw/weather/*_open_meteo.json
        ↓
data/processed/city_weather_summary.csv
        ↓
Cloud Storage + BigQuery tripsense_ai.city_weather_summary
```

```text
Places + News + Weather
        ↓
NVIDIA RAPIDS cuDF acceleration layer
        ↓
data/processed/top_places_news_weather_aware_gpu.csv
        ↓
BigQuery + Streamlit + Looker
```

Important design decision:

> Streamlit does not call live weather or air-quality APIs during page refresh. Weather and air-quality ingestion runs as a cached batch job, writes CSV output, and Streamlit reads cached results.

---

## 4. NVIDIA Acceleration Layer

TripSense AI integrates **NVIDIA RAPIDS cuDF / cudf.pandas** as the acceleration layer.

The GPU is used for tabular processing tasks:

- Loading processed CSVs
- Joining places, news, and weather data
- Detecting outdoor/weather-sensitive places
- Calculating news penalty
- Calculating weather penalty
- Computing final ranking score
- Sorting and grouping ranked places
- Running CPU vs GPU benchmark comparisons

The GPU is not used for API calls because API calls are network-bound. The NVIDIA layer is used where acceleration matters: DataFrame joins, filtering, scoring, sorting, and benchmark-scale ranking.

### Why this is suitable for TripSense AI

TripSense AI is mainly a data analytics and decision-support project. Most of the heavy work is tabular processing, which maps well to RAPIDS cuDF.

For the two-city MVP, the real dataset is small, so GPU may not always be faster than CPU. To demonstrate scalability, the benchmark script repeats the dataset to simulate a larger multi-city travel dataset and compares CPU pandas against NVIDIA RAPIDS.

Do not claim a speedup unless your benchmark files show it.

---

## 5. Tech Stack

### Application layer

- Python
- Pandas
- Streamlit
- Requests
- python-dotenv

### Data sources

- Google Places API
- GDELT DOC 2.0 API
- Open-Meteo Forecast API
- Open-Meteo Air Quality API

### Google Cloud layer

- Google Cloud Storage
- BigQuery
- Optional Looker dashboard

### NVIDIA acceleration layer

- NVIDIA GPU
- CUDA runtime/toolkit
- RAPIDS cuDF
- cudf.pandas accelerator mode

---

## 6. Project Structure

```text
TripSenseAI/
├── app/
│   └── streamlit_app.py
│
├── data/
│   ├── raw/
│   │   └── weather/
│   └── processed/
│       ├── all_cities_places_clean.csv
│       ├── place_news.csv
│       ├── place_news_summary.csv
│       ├── city_weather_summary.csv
│       ├── top_places_news_weather_aware.csv
│       ├── top_places_news_weather_aware_gpu.csv
│       ├── nvidia_benchmark_cpu.csv
│       └── nvidia_benchmark_gpu.csv
│
├── scripts/
│   ├── ingest_places.py
│   ├── clean_places.py
│   ├── ingest_news.py
│   ├── ingest_weather.py
│   ├── build_ranked_table_gpu.py
│   └── benchmark_nvidia_layer.py
│
├── src/
│   ├── weather_intelligence.py
│   ├── scoring.py
│   ├── gpu_accel.py
│   └── bigquery_io.py
│
├── requirements.txt
├── requirements-gpu.txt
├── .env.example
└── README.md
```

---

## 7. Environment Variables

Create a `.env` file from `.env.example`.

```bash
cp .env.example .env
```

Example `.env`:

```env
# Multi-city MVP
TRIPSENSE_CITIES=Jaipur,Mumbai
PLACES_MAX_RESULTS=20

# Google Places API
GOOGLE_MAPS_API_KEY=your_google_places_api_key_here

# GDELT news intelligence
NEWS_LOOKBACK_DAYS=90
GDELT_MAX_RECORDS=100
NEWS_TOP_N_PLACES=40
NEWS_CACHE_HOURS=24
GDELT_MAX_RETRIES=5

# Advanced weather risk intelligence
ENABLE_WEATHER_RISK=true
WEATHER_LOOKAHEAD_HOURS=12
WEATHER_CACHE_HOURS=3

# Rain thresholds
RAIN_MM_12H_MEDIUM=10
RAIN_MM_12H_HIGH=30
RAIN_PROB_MEDIUM=60
RAIN_PROB_HIGH=80

# Heat thresholds, using apparent temperature if available
TEMP_C_MEDIUM=35
TEMP_C_HIGH=40

# Wind and storm thresholds
WIND_KMPH_MEDIUM=35
WIND_KMPH_HIGH=50

# Air quality thresholds, using US AQI
US_AQI_MEDIUM=101
US_AQI_HIGH=151
PM25_MEDIUM=35
PM25_HIGH=55

# UV thresholds
UV_INDEX_MEDIUM=6
UV_INDEX_HIGH=8

# Visibility thresholds, meters
VISIBILITY_M_MEDIUM=3000
VISIBILITY_M_HIGH=1000

# NVIDIA acceleration
TRIPSENSE_USE_GPU=false
```

---

## 8. Local CPU Setup

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Run the normal CPU ingestion pipeline:

```bash
python scripts/ingest_places.py
python scripts/clean_places.py
python scripts/ingest_news.py
python scripts/ingest_weather.py
```

Verify outputs:

```bash
ls -lh data/processed/
```

Expected important files:

```text
all_cities_places_clean.csv
place_news_summary.csv
city_weather_summary.csv
```

---

## 9. Local NVIDIA GPU Setup on WSL2

This section is for running the NVIDIA acceleration part locally on Windows + WSL2.

### 9.1 Confirm GPU is visible inside WSL

Open Ubuntu/WSL terminal and run:

```bash
nvidia-smi
```

You should see your NVIDIA GPU listed.

Example:

```text
NVIDIA GeForce RTX 3050
CUDA Version: 13.0
```

Also confirm your distro uses WSL2 from PowerShell:

```powershell
wsl -l -v
```

The Ubuntu distro should show version `2`.

### 9.2 Install basic packages

Inside WSL:

```bash
sudo apt update
sudo apt upgrade -y

sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  git \
  build-essential \
  curl \
  wget
```

### 9.3 Keep project inside Linux filesystem

Recommended:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/TripSenseAI.git
cd TripSenseAI
```

Avoid running heavy GPU/Python work directly from `/mnt/c/...` because Windows-mounted paths are slower in WSL.

### 9.4 Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 9.5 Install CUDA toolkit inside WSL if required

Your Windows driver gives WSL GPU access, but RAPIDS may still need CUDA runtime libraries inside WSL.

For CUDA 13:

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb

sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update

sudo apt install -y cuda-toolkit-13-0
```

Add CUDA paths:

```bash
echo 'export PATH=/usr/local/cuda-13.0/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-13.0/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
nvcc --version
```

### 9.6 Install RAPIDS cuDF

For CUDA 13:

```bash
source .venv/bin/activate
python -m pip install --extra-index-url=https://pypi.nvidia.com cudf-cu13
```

For CUDA 12:

```bash
source .venv/bin/activate
python -m pip install --extra-index-url=https://pypi.nvidia.com cudf-cu12
```

Test:

```bash
python - <<'PY'
import cudf
print("cuDF is working")
print(cudf.Series([1, 2, 3]))
PY
```

---

## 10. GPU Acceleration Switch

Create or verify this file:

```text
src/gpu_accel.py
```

```python
import os


def install_gpu_acceleration() -> str:
    """
    Enables NVIDIA RAPIDS cudf.pandas only when requested.

    Important:
    This must run before importing pandas.
    """
    use_gpu = os.getenv("TRIPSENSE_USE_GPU", "false").lower() in {
        "1", "true", "yes", "gpu", "rapids"
    }

    if not use_gpu:
        return "cpu-pandas"

    try:
        import cudf.pandas
        cudf.pandas.install()
        return "gpu-rapids-cudf-pandas"
    except Exception as exc:
        print(f"[TripSenseAI] RAPIDS unavailable, falling back to CPU pandas: {exc}")
        return "cpu-pandas-fallback"
```

Important:

```python
from src.gpu_accel import install_gpu_acceleration
ACCELERATION_MODE = install_gpu_acceleration()

import pandas as pd
```

The call to `install_gpu_acceleration()` must happen before importing pandas.

---

## 11. End-to-End Run Order

### 11.1 Run ingestion and processed-data generation

```bash
source .venv/bin/activate

python scripts/ingest_places.py
python scripts/clean_places.py
python scripts/ingest_news.py
python scripts/ingest_weather.py
```

### 11.2 Build ranked table using NVIDIA GPU

```bash
TRIPSENSE_USE_GPU=true python scripts/build_ranked_table_gpu.py
```

Expected output:

```text
Acceleration mode: gpu-rapids-cudf-pandas
Rows ranked: ...
Saved: data/processed/top_places_news_weather_aware_gpu.csv
Elapsed seconds: ...
```

### 11.3 Build ranked table using CPU fallback

```bash
TRIPSENSE_USE_GPU=false python scripts/build_ranked_table_gpu.py
```

---

## 12. CPU vs GPU Benchmark

Because the MVP has only two cities, the dataset is small. The benchmark repeats rows to simulate a larger travel dataset.

For a 4 GB GPU such as RTX 3050, start with a smaller repeat count.

### CPU benchmark

```bash
TRIPSENSE_USE_GPU=false BENCHMARK_REPEAT=500 python scripts/benchmark_nvidia_layer.py
mv data/processed/nvidia_benchmark_results.csv data/processed/nvidia_benchmark_cpu.csv
```

### GPU benchmark

```bash
TRIPSENSE_USE_GPU=true BENCHMARK_REPEAT=500 python scripts/benchmark_nvidia_layer.py
mv data/processed/nvidia_benchmark_results.csv data/processed/nvidia_benchmark_gpu.csv
```

Compare:

```bash
cat data/processed/nvidia_benchmark_cpu.csv
cat data/processed/nvidia_benchmark_gpu.csv
```

Increase gradually:

```bash
TRIPSENSE_USE_GPU=true BENCHMARK_REPEAT=1000 python scripts/benchmark_nvidia_layer.py
```

If GPU memory errors occur, reduce the repeat count:

```bash
BENCHMARK_REPEAT=100
```

---

## 13. Streamlit Dashboard

Run locally:

```bash
streamlit cache clear

streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false
```

Open:

```text
http://localhost:8080
```

If running in Google Cloud Shell or another remote environment, open the forwarded web preview URL for port `8080`.

---

## 14. Recommended Streamlit GPU Output Handling

In `app/streamlit_app.py`, prefer the GPU-ranked file when available:

```python
from pathlib import Path
import pandas as pd
import streamlit as st


gpu_ranked_path = Path("data/processed/top_places_news_weather_aware_gpu.csv")
normal_ranked_path = Path("data/processed/top_places_news_weather_aware.csv")

if gpu_ranked_path.exists():
    ranked_df = pd.read_csv(gpu_ranked_path)
    acceleration_label = "NVIDIA RAPIDS cuDF accelerated ranking"
else:
    ranked_df = pd.read_csv(normal_ranked_path)
    acceleration_label = "CPU pandas ranking"

st.caption(f"Acceleration layer: {acceleration_label}")
```

Add a demo note:

```python
st.info(
    "NVIDIA acceleration layer: TripSense AI uses RAPIDS cuDF/cudf.pandas "
    "to accelerate tabular joins, scoring, weather/news penalties, and ranking."
)
```

---

## 15. Google Cloud Upload and BigQuery Load

Set project variables:

```bash
export PROJECT_ID="tripsense-ai-sumit-2026"
export REGION="asia-south1"
export BUCKET_NAME="${PROJECT_ID}-data"

gcloud config set project $PROJECT_ID
```

Upload raw and processed data:

```bash
gcloud storage cp -r data/raw gs://$BUCKET_NAME/
gcloud storage cp -r data/processed gs://$BUCKET_NAME/
```

Load main tables:

```bash
bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.places \
  data/processed/all_cities_places_clean.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.place_news_summary \
  data/processed/place_news_summary.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.city_weather_summary \
  data/processed/city_weather_summary.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.top_places_news_weather_aware_gpu \
  data/processed/top_places_news_weather_aware_gpu.csv
```

Load benchmark evidence:

```bash
bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.nvidia_benchmark_cpu \
  data/processed/nvidia_benchmark_cpu.csv

bq load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  $PROJECT_ID:tripsense_ai.nvidia_benchmark_gpu \
  data/processed/nvidia_benchmark_gpu.csv
```

---

## 16. BigQuery Dashboard SQL

Create the joined dashboard table:

```sql
CREATE OR REPLACE TABLE `tripsense-ai-sumit-2026.tripsense_ai.place_dashboard` AS
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
  IFNULL(n.latest_article_title, '') AS latest_article_title,
  IFNULL(n.latest_article_url, '') AS latest_article_url,

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

FROM `tripsense-ai-sumit-2026.tripsense_ai.places` p
LEFT JOIN `tripsense-ai-sumit-2026.tripsense_ai.place_news_summary` n
USING (place_id)
LEFT JOIN `tripsense-ai-sumit-2026.tripsense_ai.city_weather_summary` w
ON LOWER(p.city) = LOWER(w.city);
```

Create the final ranked table:

```sql
CREATE OR REPLACE TABLE `tripsense-ai-sumit-2026.tripsense_ai.top_places_news_weather_aware` AS
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

FROM `tripsense-ai-sumit-2026.tripsense_ai.place_dashboard`
ORDER BY news_weather_adjusted_score DESC;
```

---

## 17. Validation Checklist

| Check | Expected result |
|---|---|
| Jaipur and Mumbai exist | `df['city'].value_counts()` shows both cities |
| Weather summary generated | `city_weather_summary.csv` exists |
| Weather summary has risk fields | Includes `heat_risk_level`, `air_quality_risk_level`, `uv_risk_level`, `visibility_risk_level` |
| Mumbai rain warning works | `weather_risk_level` becomes Medium/High during heavy rain |
| Jaipur heat warning works | `heat_risk_level` becomes Medium/High when apparent temperature crosses threshold |
| Outdoor ranking changed | Outdoor places show `weather_penalty` |
| GPU ranked file exists | `top_places_news_weather_aware_gpu.csv` exists |
| CPU benchmark exists | `nvidia_benchmark_cpu.csv` exists |
| GPU benchmark exists | `nvidia_benchmark_gpu.csv` exists |
| BigQuery dashboard updated | `place_dashboard` has weather sub-risk columns |
| Looker / dashboard source | Uses `top_places_news_weather_aware` or `top_places_news_weather_aware_gpu` |

Quick validation command:

```bash
python - <<'PY'
import pandas as pd

for path in [
    'data/processed/all_cities_places_clean.csv',
    'data/processed/place_news_summary.csv',
    'data/processed/city_weather_summary.csv',
    'data/processed/top_places_news_weather_aware_gpu.csv',
]:
    print('\n', path)
    df = pd.read_csv(path)
    print(df.head())
    if 'city' in df.columns:
        print(df['city'].value_counts())
PY
```

---

## 18. Troubleshooting

### `gcloud: command not found`

Use Google Cloud Shell if possible because `gcloud` is preinstalled there.

For local WSL, install Google Cloud CLI using Google’s Linux installation method, then run:

```bash
gcloud auth login
gcloud config set project tripsense-ai-sumit-2026
```

### Streamlit says `.port` is not a Python file

Wrong:

```bash
streamlit run app/streamlit_app.py--server.port 8080
```

Correct:

```bash
streamlit run app/streamlit_app.py --server.port 8080
```

There must be a space between `.py` and `--server.port`.

### Cloud Shell WebSocket origin rejected

Use:

```bash
streamlit run app/streamlit_app.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false
```

### `ModuleNotFoundError: No module named 'cudf'`

Activate the environment and install the matching RAPIDS package:

```bash
source .venv/bin/activate
python -m pip install --extra-index-url=https://pypi.nvidia.com cudf-cu13
```

For CUDA 12:

```bash
python -m pip install --extra-index-url=https://pypi.nvidia.com cudf-cu12
```

### `libcudart.so.13 not found`

Install CUDA toolkit inside WSL:

```bash
sudo apt install -y cuda-toolkit-13-0
source ~/.bashrc
```

### GPU memory error on RTX 3050 4 GB

Reduce benchmark repeat count:

```bash
TRIPSENSE_USE_GPU=true BENCHMARK_REPEAT=100 python scripts/benchmark_nvidia_layer.py
```

Then increase slowly:

```bash
BENCHMARK_REPEAT=500
BENCHMARK_REPEAT=1000
```

### GPU is slower than CPU on tiny dataset

This can happen for small data because GPU startup and data transfer overhead can dominate runtime.

For hackathon explanation, say:

> The two-city MVP is intentionally small, so the GPU benchmark repeats records to simulate a larger multi-city travel dataset. This demonstrates how the same ranking logic can scale when TripSense AI expands beyond Jaipur and Mumbai.

---

## 19. Hackathon Demo Explanation

Use this explanation during the demo:

```text
TripSense AI does not only rank places by rating and popularity.
It adds a Live Context Layer with three major signals:

1. GDELT news intelligence
   Detects recent incidents, viral issues, closures, crowds, and disruptions.

2. Advanced weather intelligence
   Detects rain, heat, wind/storms, poor visibility, and UV risk.

3. Air quality intelligence
   Detects unhealthy AQI and PM2.5/PM10 conditions.

The app reduces the score of outdoor or weather-sensitive places during risky conditions.
This helps a traveller decide not just where places are popular, but where it is sensible to go today.

For the NVIDIA acceleration layer, TripSense AI uses RAPIDS cuDF/cudf.pandas to accelerate the batch ranking pipeline.
The GPU layer performs joins, filtering, penalty calculation, sorting, and ranking over the processed tourism dataset.
The project also includes CPU and GPU benchmark artifacts to show the acceleration layer working.
```

---

## 20. Submission Artifacts

Include these files/screenshots in the final submission:

```text
README.md
requirements.txt
requirements-gpu.txt
.env.example
src/gpu_accel.py
src/weather_intelligence.py
src/scoring.py
scripts/ingest_weather.py
scripts/build_ranked_table_gpu.py
scripts/benchmark_nvidia_layer.py
data/processed/city_weather_summary.csv
data/processed/top_places_news_weather_aware_gpu.csv
data/processed/nvidia_benchmark_cpu.csv
data/processed/nvidia_benchmark_gpu.csv
screenshots/streamlit_live_context.png
screenshots/nvidia_benchmark_result.png
```

---

## 21. Sources

- Open-Meteo Forecast API: https://open-meteo.com/en/docs
- Open-Meteo Air Quality API: https://open-meteo.com/en/docs/air-quality-api
- GDELT Project: https://www.gdeltproject.org/
- RAPIDS cuDF: https://docs.rapids.ai/api/cudf/stable/
- RAPIDS cudf.pandas: https://docs.rapids.ai/api/cudf/stable/cudf_pandas/
- NVIDIA CUDA on WSL: https://docs.nvidia.com/cuda/wsl-user-guide/index.html
- Google Cloud BigQuery: https://cloud.google.com/bigquery/docs
- Google Cloud Storage: https://cloud.google.com/storage/docs

---

## 22. Current MVP Status

Current MVP scope:

```text
Cities: Jaipur + Mumbai
Data: Places + GDELT + Weather + Air Quality
Cloud: GCS + BigQuery
App: Streamlit
Acceleration: NVIDIA RAPIDS cuDF/cudf.pandas
Submission proof: GPU ranked CSV + CPU/GPU benchmark CSVs
```

