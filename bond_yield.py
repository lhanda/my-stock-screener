import requests
import json
import os
import time

CACHE_FILE = os.path.expanduser("~/.cache/fred_aaa_yield_cache.json")
os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
CACHE_TTL = 24 * 3600  # 24 hours

def get_latest_aaa_yield_fred(api_key):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
            if time.time() - cache.get("timestamp", 0) < CACHE_TTL:
                return cache["value"]

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "AAA",
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    observations = data.get("observations", [])
    if not observations:
        raise ValueError("No observations returned from FRED API")

    latest_value = observations[0]["value"]
    try:
        latest_yield = float(latest_value)
    except ValueError:
        raise ValueError(f"Invalid yield value received: {latest_value}")

    with open(CACHE_FILE, "w") as f:
        json.dump({"timestamp": time.time(), "value": latest_yield}, f)

    return latest_yield

if __name__ == "__main__":
    API_KEY = os.getenv("FRED_API_KEY")
    if not API_KEY:
        print("Please set the FRED_API_KEY environment variable")
        exit(1)

    try:
        yield_aaa = get_latest_aaa_yield_fred(API_KEY)
        print(f"Latest 20Y AAA bond yield: {yield_aaa}%")
    except Exception as e:
        print("Error fetching AAA bond yield:", e)
