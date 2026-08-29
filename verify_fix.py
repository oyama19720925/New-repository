# verify_fix.py
import requests

API_KEY  = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
API_BASE = "https://api.jquants.com/v2"

code = "72030"
url  = f"{API_BASE}/fins/summary"
resp = requests.get(url, headers={"X-API-KEY": API_KEY},
                    params={"code": code}, timeout=10)

data = resp.json()
items = data.get("data", [])  # ← 修正後
print(f"items数: {len(items)}")

if items:
    item = items[-1]  # 最新
    print(f"DiscDate: {item.get('DiscDate')}")
    print(f"EPS:  {item.get('EPS')}")
    print(f"BPS:  {item.get('BPS')}")
    print(f"ROE:  {item.get('ROE')}")
    print(f"FEPS: {item.get('FEPS')}")
    print(f"FDivAnn: {item.get('FDivAnn')}")