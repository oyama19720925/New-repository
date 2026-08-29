# C:\stock_system\check_calendar.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
BASE_URL = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

r = requests.get(
    f"{BASE_URL}/markets/calendar",
    headers=HEADERS,
    params={
        "from": "2026-08-10",
        "to": "2026-08-20"
    }
)

print(f"Status: {r.status_code}")
data = r.json().get("data", [])
print(f"件数: {len(data)}")
print()
for d in data:
    print(d)