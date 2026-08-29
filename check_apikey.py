# check_apikey.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY")

print(f"📋 APIキー確認: {API_KEY[:10]}...{API_KEY[-5:] if API_KEY else 'None'}")
print(f"   文字数: {len(API_KEY) if API_KEY else 0}")

# ヘッダーパターンを複数試す
BASE_URL = "https://api.jquants.com"
test_url = BASE_URL + "/markets/calendar"

patterns = [
    {"x-api-key": API_KEY},
    {"Authorization": f"Bearer {API_KEY}"},
    {"apikey": API_KEY},
]

for headers in patterns:
    key_name = list(headers.keys())[0]
    resp = requests.get(test_url, headers=headers, timeout=10)
    print(f"\n🔑 ヘッダー [{key_name}]: status={resp.status_code}")
    print(f"   レスポンス: {resp.text[:200]}")