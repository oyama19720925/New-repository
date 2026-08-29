# test_fins_api.py
import requests

API_KEY  = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
API_BASE = "https://api.jquants.com/v2"

# スクリーニング結果の先頭銘柄で試す（例: 7203トヨタ）
for code in ["72030", "7203", "13010", "1301"]:
    url = f"{API_BASE}/fins/summary"
    resp = requests.get(url, headers={"X-API-KEY": API_KEY},
                        params={"code": code}, timeout=10)
    print(f"code={code} status={resp.status_code}")
    data = resp.json()
    items = data.get("fins_summary", [])
    print(f"  items数: {len(items)}")
    if items:
        print(f"  最新: {items[-1]}")
    else:
        print(f"  レスポンス全体: {data}")
    print()