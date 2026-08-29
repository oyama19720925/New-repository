# check_fins_summary.py として保存・実行
import requests
import json

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

resp = requests.get(
    f"{BASE}/fins/summary",
    headers=HEADERS,
    params={"code": "7203"},
    timeout=10
)

data = resp.json()

# 最新1件のキー一覧を表示
if data.get("data"):
    latest = data["data"][-1]  # 最新
    print("=== 利用可能なフィールド一覧 ===")
    for k, v in latest.items():
        print(f"  {k}: {v}")