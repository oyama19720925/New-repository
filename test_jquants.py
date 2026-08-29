import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
EMAIL = "oyama@miomio.jp"
PASSWORD = "347447498885Mm"
BASE_URL = "https://api.jquants.com/v2"

# 1. リフレッシュトークン取得
url = f"{BASE_URL}/auth/refresh_token"
payload = {
    "mail": EMAIL,
    "password": PASSWORD
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=payload)
print(f"ステータスコード: {response.status_code}")
print(f"レスポンス: {response.text}")

if response.status_code == 200:
    refresh_token = response.json().get("refreshToken")
    
    # 2. IDトークン取得
    url = f"{BASE_URL}/auth/id_token"
    payload = {
        "refreshToken": refresh_token
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス: {response.text}")