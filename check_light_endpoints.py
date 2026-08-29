# check_light_endpoints.py
import requests

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

endpoints = [
    # 市場情報
    "/markets/calendar",
    "/markets/trading_calendar",
    "/markets/short_selling",
    "/markets/breakdown",
    # 株価
    "/equities/daily_quotes",
    "/equities/prices",
    "/equities/prices/daily_quotes",
    "/equities/bars",
    "/equities/bars/daily",
    # マスター
    "/equities/master",
    "/equities/sections",
    "/equities/info",
    # 財務
    "/fins/statements",
    "/fins/summary",
    "/fins/fs_details",
    "/fins/dividend",
    # 指数
    "/indices",
    "/indices/topix",
    "/indices/daily_quotes",
    # オプション
    "/option/index_option",
    # 信用
    "/markets/margin_trading",
]

print("=" * 60)
print(f"{'エンドポイント':<40} {'結果'}")
print("=" * 60)

for ep in endpoints:
    url = BASE + ep
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            icon = "✅ OK"
        elif resp.status_code == 400:
            icon = "🟡 要パラメータ(400)"
        elif resp.status_code == 403:
            icon = "❌ プラン制限(403)"
        elif resp.status_code == 404:
            icon = "⚠️  Not Found(404)"
        else:
            icon = f"❓ {resp.status_code}"
        print(f"{ep:<40} {icon}")
    except Exception as e:
        print(f"{ep:<40} ⚠️  ERR: {e}")

print("=" * 60)