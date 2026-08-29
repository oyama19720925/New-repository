import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
headers = {"X-API-KEY": API_KEY}

# テスト用：トヨタ
url = "https://api.jquants.com/v1/fins/summary"
params = {"code": "72030"}
r = requests.get(url, headers=headers, params=params)
print("Status:", r.status_code)
print("Keys:", list(r.json().keys()) if r.status_code == 200 else r.text)
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print("件数:", len(items))
    if items:
        print("最初のレコード:", items[0])