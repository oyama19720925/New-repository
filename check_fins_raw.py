import requests
import json

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
headers = {"X-API-KEY": API_KEY}
BASE = "https://api.jquants.com/v2"

code = "7203"

r = requests.get(f"{BASE}/fins/summary", headers=headers, params={"code": code})
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    records = data.get("data", [])
    print(f"レコード数: {len(records)}")

    if records:
        latest = records[-1]
        print("\n=== 実際のキー名と値 全件 ===")
        for k, v in sorted(latest.items()):
            print(f"  '{k}' : {repr(v)}")
        
        print("\n=== JSONそのまま ===")
        print(json.dumps(latest, ensure_ascii=False, indent=2))
else:
    print(r.text)