import requests

BASE_URL = "https://api.jquants.com/v2"
API_KEY  = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"

TEST_CODE = "72030"  # トヨタ

# 試す認証ヘッダーのパターン
auth_patterns = [
    {"Authorization": f"Bearer {API_KEY}"},
    {"Authorization": f"Token {API_KEY}"},
    {"Authorization": API_KEY},
    {"X-API-KEY": API_KEY},
    {"apikey": API_KEY},
]

endpoints = [
    f"{BASE_URL}/fins/summary?code={TEST_CODE}",
    f"{BASE_URL}/fins/summary?code={TEST_CODE[:4]}",
    f"{BASE_URL}/fins/statements?code={TEST_CODE}",
]

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"URL: {endpoint}")
    print('='*60)
    for headers in auth_patterns:
        try:
            res = requests.get(endpoint, headers=headers, timeout=10)
            print(f"  ヘッダー: {list(headers.keys())[0]:20} | status: {res.status_code} | {res.text[:100]}")
            if res.status_code == 200:
                print("  ✅ 成功！")
        except Exception as e:
            print(f"  ❌ エラー: {e}")