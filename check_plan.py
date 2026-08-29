import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
headers = {"X-API-KEY": API_KEY}
BASE = "https://api.jquants.com/v2"

# 各エンドポイントを試す
endpoints = [
    ("/fins/summary", {"code": "72030"}),
    ("/fins/statements", {"code": "72030"}),
    ("/fins/announcement", {}),
    ("/equities/master", {"code": "72030"}),
    ("/markets/calendar", {}),
    ("/equities/bars/daily", {"code": "72030"}),
]

for path, params in endpoints:
    r = requests.get(BASE + path, headers=headers, params=params)
    status = r.status_code
    if status == 200:
        keys = list(r.json().keys())
        print(f"✅ {path}: {status} - keys={keys}")
    else:
        print(f"❌ {path}: {status} - {r.text[:80]}")