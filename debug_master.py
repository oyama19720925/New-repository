import os
import requests

API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
headers = {"x-api-key": API_KEY}
url = "https://api.jquants.com/v2/equities/master"

resp = requests.get(url, headers=headers, params={"code": "72030"}, timeout=15)
print("ステータスコード:", resp.status_code)
print("レスポンスJSON全体:")
print(resp.json())