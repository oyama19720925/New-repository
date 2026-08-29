# C:\stock_system\test_detail.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY")

print(f"APIキー: {API_KEY}")
print(f"キー長: {len(API_KEY)} 文字")
print()

BASE_URL = "https://api.jquants.com/v2"

# パターン1: x-api-keyのみ
print("=== パターン1: x-api-key ヘッダー ===")
r = requests.get(
    f"{BASE_URL}/listed/info",
    headers={"x-api-key": API_KEY}
)
print(f"ステータス: {r.status_code}")
print(f"レスポンス: {r.text[:300]}")
print()

# パターン2: Authorizationのみ
print("=== パターン2: Authorization Bearer ===")
r = requests.get(
    f"{BASE_URL}/listed/info",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
print(f"ステータス: {r.status_code}")
print(f"レスポンス: {r.text[:300]}")
print()

# パターン3: クエリパラメータ
print("=== パターン3: クエリパラメータ ===")
r = requests.get(
    f"{BASE_URL}/listed/info",
    params={"apikey": API_KEY}
)
print(f"ステータス: {r.status_code}")
print(f"レスポンス: {r.text[:300]}")
print()

# パターン4: 別エンドポイント（プラン確認）
print("=== パターン4: /token/auth_user (V1) ===")
r = requests.post(
    "https://api.jquants.com/v1/token/auth_user",
    json={"mailaddress": "test@test.com", "password": "test"}
)
print(f"ステータス: {r.status_code}")
print(f"レスポンス: {r.text[:300]}")
print()

# パターン5: V2 markets endpoint
print("=== パターン5: /markets/trading_calendar ===")
r = requests.get(
    f"{BASE_URL}/markets/trading_calendar",
    headers={"x-api-key": API_KEY}
)
print(f"ステータス: {r.status_code}")
print(f"レスポンス: {r.text[:300]}")