import requests

BASE_URL = "https://api.jquants.com/v1"

# ===== ここにJ-Quantsのログイン情報を入力 =====
MAIL     = "oyama@miomio.jp"   # 例: sample@gmail.com
PASSWORD = "347447498885Mm"        # 例: MyPass123
# =============================================

TEST_CODE = "72030"  # トヨタ（5桁）

print("=" * 50)
print("Step1: メール/パスワードでrefreshToken取得")
print("=" * 50)

res1 = requests.post(
    f"{BASE_URL}/token/auth_user",
    json={"mailaddress": MAIL, "password": PASSWORD}
)
print(f"status: {res1.status_code}")
print(f"body  : {res1.text[:300]}")

if res1.status_code != 200:
    print("❌ ログイン失敗。メールアドレスとパスワードを確認してください")
    exit()

refresh_token = res1.json().get("refreshToken", "")
print(f"\n✅ refreshToken: {refresh_token[:30]}...")

print("\n" + "=" * 50)
print("Step2: refreshToken → idToken取得")
print("=" * 50)

res2 = requests.post(
    f"{BASE_URL}/token/auth_refresh",
    params={"refreshtoken": refresh_token}
)
print(f"status: {res2.status_code}")
print(f"body  : {res2.text[:300]}")

if res2.status_code != 200:
    print("❌ idToken取得失敗")
    exit()

id_token = res2.json().get("idToken", "")
print(f"\n✅ idToken: {id_token[:30]}...")

print("\n" + "=" * 50)
print("Step3: fins/summary 取得")
print("=" * 50)

# 4桁で試す
for code in [TEST_CODE, TEST_CODE[:4]]:
    res3 = requests.get(
        f"{BASE_URL}/fins/summary",
        headers={"Authorization": f"Bearer {id_token}"},
        params={"code": code}
    )
    print(f"\n銘柄コード [{code}] status: {res3.status_code}")
    print(f"body: {res3.text[:500]}")