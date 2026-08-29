# C:\stock_system\test_v2_endpoints.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")

BASE_URL = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

endpoints = [
    "/equities/master",
    "/equities/bars/daily",
    "/fins/summary",
    "/fins/details",
    "/fins/dividend",
    "/markets/calendar",
    "/indices/bars/daily",
    "/markets/margin-interest",
]

print("=" * 60)
print("J-Quants API V2 エンドポイントテスト")
print("=" * 60)

for ep in endpoints:
    url = BASE_URL + ep
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        icon = "✅" if r.status_code == 200 else "❌" if r.status_code == 403 else "⚠️"
        print(f"{icon} [{r.status_code}] {ep}")
        if r.status_code == 200:
            print(f"   → {str(r.json())[:100]}")
        else:
            print(f"   → {r.text[:80]}")
    except Exception as e:
        print(f"💥 {ep} → {e}")

print("=" * 60)