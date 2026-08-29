# C:\stock_system\test_jpx.py
import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
HEADERS = {"x-api-key": API_KEY}

BASE = "https://jpx-jquants.com"

PATHS = [
    "/v2/listed/info",
    "/v1/listed/info",
    "/api/v2/listed/info",
    "/api/v1/listed/info",
    "/v2/markets/trading_calendar",
    "/v1/markets/trading_calendar",
    "/v2/prices/daily_quotes",
    "/v1/prices/daily_quotes",
    "/v2/fins/statements",
    "/v1/fins/statements",
    "/v2/fins/announcement",
    "/v1/fins/announcement",
]

print(f"ベースURL: {BASE}\n")
for path in PATHS:
    url = BASE + path
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        status = r.status_code
        body = r.text[:200]

        if status == 200:
            print(f"✅✅✅ 成功！ [{status}] {url}")
            print(f"   → {body}\n")
        elif status == 403:
            msg = ""
            try:
                msg = r.json().get("message", "")[:100]
            except:
                msg = r.text[:100]
            print(f"🔑 [{status}] {url}")
            print(f"   → {msg}\n")
        elif status == 404:
            print(f"❓ [{status}] {url} （パス不明）\n")
        elif status == 401:
            print(f"🔐 [{status}] {url} （認証エラー）\n")
        else:
            print(f"⚠️  [{status}] {url}")
            print(f"   → {body}\n")
    except Exception as e:
        print(f"❌ [ERROR] {url}")
        print(f"   → {str(e)[:80]}\n")