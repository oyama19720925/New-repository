import requests, json

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
headers = {"X-API-KEY": API_KEY}
BASE = "https://api.jquants.com/v2"

r = requests.get(f"{BASE}/fins/summary", headers=headers, params={"code": "72030"})
data = r.json().get("data", [])

if data:
    print("=== 最新レコードの全キー ===")
    latest = data[-1]
    for k, v in latest.items():
        print(f"  {k}: {v}")
else:
    print("データなし")