import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

tests = [
    ("/equities/daily_quotes", {"code": "7203", "date": "2025-08-01"}),
    ("/equities/prices/daily_quotes", {"code": "7203", "date": "2025-08-01"}),
    ("/equities/master", {"code": "7203"}),
    ("/fins/statements", {"code": "7203"}),
    ("/fins/summary", {"code": "7203"}),
]

for ep, params in tests:
    url = BASE + ep
    resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
    icon = "OK" if resp.status_code == 200 else "NG"
    print(f"{icon} [{resp.status_code}] {ep}")
    if resp.status_code == 200:
        print(f"   -> {resp.text[:200]}")
    else:
        print(f"   -> {resp.text[:100]}")