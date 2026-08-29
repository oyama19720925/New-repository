# C:\stock_system\test_find_url.py
import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
HEADERS = {"x-api-key": API_KEY}

# 試すベースURL一覧
BASE_URLS = [
    "https://api.jquants.com",
    "https://jquants.com",
    "https://jpx-jquants.com",
    "https://api.jpx.co.jp/jquants",
    "https://jquants-api.com",
]

# 試すエンドポイントパス一覧
PATHS = [
    "/v2/listed/info",
    "/v1/listed/info",
    "/api/v2/listed/info",
    "/api/v1/listed/info",
]

print("=== URL探索テスト ===\n")
for base in BASE_URLS:
    for path in PATHS:
        url = base + path
        try:
            r = requests.get(url, headers=HEADERS, timeout=5)
            status = r.status_code
            body = r.text[:150]
            
            if status == 200:
                print(f"✅✅✅ 成功！ [{status}] {url}")
                print(f"   → {body}\n")
            elif status == 403:
                msg = r.json().get("message", "")[:80] if r.text.startswith("{") else r.text[:80]
                print(f"🔑 [{status}] {url}")
                print(f"   → {msg}\n")
            elif status == 404:
                print(f"❓ [{status}] {url} （エンドポイント不明）\n")
            else:
                print(f"⚠️  [{status}] {url}\n")
        except Exception as e:
            print(f"❌ [ERROR] {url}")
            print(f"   → {str(e)[:100]}\n")