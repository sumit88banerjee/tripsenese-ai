import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import bigquery
sys.path.append(str(Path(__file__).resolve().parents[1]))
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
DATASET = os.getenv("BIGQUERY_DATASET", "tripsense_ai")
if not PROJECT_ID:
    raise RuntimeError("GOOGLE_CLOUD_PROJECT missing in .env")
client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.places"
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)
with open("data/processed/jaipur_places_clean.csv", "rb") as source_file:
    job = client.load_table_from_file(source_file, table_id, job_config=job_config)
job.result()
table = client.get_table(table_id)
print(f"Loaded {table.num_rows} rows into {table_id}")