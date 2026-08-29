# check_no_code.py
import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL = "https://api.jquants.com/v2"
HEADERS  = {"x-api-key": API_KEY}

print("=" * 60)

# テスト1: codeなし、fromのみ
url = BASE_URL + "/equities/bars/daily"

tests = [
    {"from": "2026-08-19", "to": "2026-08-19"},
    {"date": "2026-08-19"},
    {},
]

for params in tests:
    print(f"\nparams: {params}")
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    print(f"status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        keys = list(data.keys())
        print(f"keys: {keys}")
        for k in keys:
            v = data[k]
            if isinstance(v, list):
                print(f"  [{k}] {len(v)}件")
                if v:
                    import json
                    print(f"  先頭1件: {json.dumps(v[0], ensure_ascii=False, indent=2)}")
    else:
        print(f"body: {resp.text[:200]}")

print("\n" + "=" * 60)