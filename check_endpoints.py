# check_endpoints.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY")
HEADERS = {"x-api-key": API_KEY}
BASE_URL = "https://api.jquants.com"

# テスト対象エンドポイント一覧
endpoints = [
    # 株価系
    "/equities/bars/daily",
    "/equities/bars",
    "/equities/daily_quotes",
    "/equities/prices",
    "/equities/prices/daily_quotes",
    # マスター系（以前200だった）
    "/equities/master",
    # 財務系
    "/fins/summary",
    "/fins/statements",
    "/fins/fs_details",
    # 市場系
    "/markets/calendar",
    "/markets/trading_calendar",
    # インデックス系
    "/indices",
    "/indices/topix",
]

print("=" * 60)
print("🔍 エンドポイント アクセステスト")
print("=" * 60)

for ep in endpoints:
    url = BASE_URL + ep
    try:
        # パラメータなしでテスト
        resp = requests.get(url, headers=HEADERS, timeout=10)
        status = resp.status_code
        
        if status == 200:
            icon = "✅"
            detail = f"OK - keys={list(resp.json().keys())[:3]}"
        elif status == 400:
            icon = "⚠️ "
            detail = "Bad Request（パラメータ必要）→ アクセス可能！"
        elif status == 403:
            icon = "❌"
            detail = "Forbidden（プラン制限）"
        elif status == 404:
            icon = "🔷"
            detail = "Not Found（エンドポイント不明）"
        else:
            icon = "❓"
            detail = f"status={status}"
            
        print(f"{icon} {ep:<40} → {detail}")
        
    except Exception as e:
        print(f"💥 {ep:<40} → エラー: {e}")

print("=" * 60)