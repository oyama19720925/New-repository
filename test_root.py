# C:\stock_system\test_root.py
import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
HEADERS = {"x-api-key": API_KEY}

# ルートやよく使われるパスを試す
URLS = [
    # jpx-jquants.com のルート探索
    "https://jpx-jquants.com/",
    "https://jpx-jquants.com/api",
    "https://jpx-jquants.com/api/",
    "https://jpx-jquants.com/spec",
    "https://jpx-jquants.com/docs",
    "https://jpx-jquants.com/swagger",
    "https://jpx-jquants.com/openapi",
    "https://jpx-jquants.com/openapi.json",
    "https://jpx-jquants.com/swagger.json",

    # AWS API Gateway 形式（よく使われる）
    "https://api.jquants.com/",
    "https://api.jquants.com/v1",
    "https://api.jquants.com/v2",

    # 別のサブドメイン
    "https://data.jquants.com/v2/listed/info",
    "https://market.jquants.com/v2/listed/info",
]

for url in URLS:
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        status = r.status_code
        body = r.text[:300]
        ct = r.headers.get("Content-Type", "")

        if status == 200:
            print(f"✅✅✅ [{status}] {url}")
            print(f"   Content-Type: {ct}")
            print(f"   → {body[:200]}\n")
        else:
            print(f"[{status}] {url}")
            print(f"   → {body[:150]}\n")
    except Exception as e:
        print(f"❌ {url}")
        print(f"   → {str(e)[:80]}\n")