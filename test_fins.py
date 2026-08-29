import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL = "https://api.jquants.com/v2"

# テスト対象銘柄（複数試す）
codes = ["19510", "1951", "72030", "7203"]

for code in codes:
    url = f"{BASE_URL}/fins/summary"
    headers = {"X-API-KEY": API_KEY}
    params = {"code": code}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"code={code} | status={resp.status_code} | body={resp.text[:200]}")
    print("-" * 60)