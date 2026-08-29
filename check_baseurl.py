# check_baseurl.py
import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
HEADERS = {"x-api-key": API_KEY}

# 試すURLパターン
urls = [
    "https://api.jquants.com/v1/markets/trading_calendar",
    "https://api.jquants.com/v2/markets/trading_calendar",
    "https://api.jquants.com/markets/trading_calendar",
    "https://api.jquants.com/v1/markets/calendar",
    "https://api.jquants.com/v2/markets/calendar",
    "https://api.jquants.com/markets/calendar",
    "https://jquants-api.com/v1/markets/trading_calendar",
    "https://jquants-api.com/v2/markets/trading_calendar",
]

for url in urls:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        icon = "✅" if resp.status_code == 200 else "❌"
        print(f"{icon} [{resp.status_code}] {url}")
        if resp.status_code == 200:
            print(f"   → {resp.text[:150]}")
    except Exception as e:
        print(f"⚠️  [ERR] {url} → {e}")