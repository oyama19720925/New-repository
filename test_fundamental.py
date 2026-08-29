import requests
import json

# ── 設定 ──────────────────────────────────────────
API_KEY   = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL  = "https://api.jquants.com/v1"
TEST_CODE = "7203"  # トヨタ

# ── Step1: トークン取得 ───────────────────────────
def get_token():
    url = f"{BASE_URL}/token/auth_user"
    res = requests.post(url, json={"mailaddress": "", "password": ""})
    print(f"[Token] status: {res.status_code}")
    print(f"[Token] body  : {res.text[:200]}")
    return res.json().get("idToken", "")

# ── Step2: リフレッシュトークンでIDトークン取得 ───
def get_token_v2():
    # リフレッシュトークン方式
    refresh_url = f"{BASE_URL}/token/auth_refresh"
    res = requests.post(
        refresh_url,
        params={"refreshtoken": API_KEY}
    )
    print(f"[Refresh] status: {res.status_code}")
    print(f"[Refresh] body  : {res.text[:300]}")
    return res.json().get("idToken", "")

# ── Step3: fins/summary 取得 ─────────────────────
def get_fins(token, code):
    url = f"{BASE_URL}/fins/summary"
    headers = {"Authorization": f"Bearer {token}"}
    params  = {"code": code}
    res = requests.get(url, headers=headers, params=params)
    print(f"\n[fins/summary] status: {res.status_code}")
    print(f"[fins/summary] body  : {res.text[:500]}")

# ── 実行 ─────────────────────────────────────────
print("=" * 50)
print(f"テスト銘柄: {TEST_CODE}")
print("=" * 50)

token = get_token_v2()
if token:
    print(f"\n✅ トークン取得成功: {token[:30]}...")
    get_fins(token, TEST_CODE)
else:
    print("\n❌ トークン取得失敗")
    print("APIキーを直接使用して試行...")
    # APIキー直接使用
    url = f"{BASE_URL}/fins/summary"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params  = {"code": TEST_CODE}
    res = requests.get(url, headers=headers, params=params)
    print(f"[直接] status: {res.status_code}")
    print(f"[直接] body  : {res.text[:500]}")