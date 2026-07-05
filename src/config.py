import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def get_cities() -> list[str]:
    value = os.getenv("TRIPSENSE_CITIES", "Jaipur,Mumbai")
    cities = [item.strip() for item in value.split(",") if item.strip()]
    if not cities:
        raise RuntimeError("TRIPSENSE_CITIES is empty. Example: Jaipur,Mumbai")
    return cities


def slugify(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return None
