# check_bars.py
import requests, json

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

# パラメータパターンをいくつか試す
tests = [
    {"code": "7203"},
    {"code": "7203", "date_from": "2026-08-01", "date_to": "2026-08-18"},
    {"code": "7203", "from": "2026-08-01", "to": "2026-08-18"},
    {"code": "7203", "start_date": "2026-08-01", "end_date": "2026-08-18"},
]

for params in tests:
    url = BASE_URL + "/equities/bars/daily"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    print(f"\n{'='*50}")
    print(f"params: {params}")
    print(f"status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        # キー確認
        print(f"keys: {list(data.keys())}")
        # 最初のキーのデータ件数と先頭2件表示
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  [{k}] {len(v)}件")
                if v:
                    print(f"  先頭1件: {json.dumps(v[0], ensure_ascii=False, indent=2)}")
                    print(f"  末尾1件: {json.dumps(v[-1], ensure_ascii=False, indent=2)}")
                break
    else:
        print(f"body: {resp.text[:300]}")