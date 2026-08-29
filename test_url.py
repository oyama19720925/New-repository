# C:\stock_system\test_url.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY")
headers = {"x-api-key": API_KEY}

# テストするURL一覧
urls = [
    "https://api.jquants.com/v2/listed/info",
    "https://api.jpx-jquants.com/v2/listed/info",
    "https://api.jquants.com/api/v2/listed/info",
    "https://api.jquants.com/v1/listed/info",
    "https://api.jpx-jquants.com/v1/listed/info",
]

for url in urls:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        status = response.status_code
        icon = "✅" if status == 200 else "❌"
        print(f"{icon} [{status}] {url}")
        if status == 200:
            print(f"   → 正解URL発見！")
            import json
            data = response.json()
            keys = list(data.keys())
            print(f"   → レスポンスキー: {keys}")
    except Exception as e:
        print(f"⚠️ [ERROR] {url}")
        print(f"   → {e}")

print("\n完了")