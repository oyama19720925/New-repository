# test_jquants_v2.py
import requests
import json

# ============================================
# 🔐 J-Quants API設定
# ============================================
EMAIL = "oyama@miomio.jp"
PASSWORD = "347447498885Mm"
BASE_URL = "https://api.jquants.com/v2"

print("=" * 60)
print("🔍 J-Quants API テスト")
print("=" * 60)

# 1️⃣ リフレッシュトークン取得
print("\n1️⃣ リフレッシュトークン取得中...")
url = f"{BASE_URL}/auth/refresh_token"
payload = {
    "mail": EMAIL,
    "password": PASSWORD
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"  ステータスコード: {response.status_code}")
    print(f"  レスポンス: {response.text}")
    
    if response.status_code == 200:
        refresh_token = response.json().get("refreshToken")
        print(f"✅ リフレッシュトークン取得成功: {refresh_token[:20]}...")
        
        # 2️⃣ IDトークン取得
        print("\n2️⃣ IDトークン取得中...")
        url = f"{BASE_URL}/auth/id_token"
        payload = {
            "refreshToken": refresh_token
        }
        
        response = requests.post(url, headers=headers, json=payload)
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.text}")
        
        if response.status_code == 200:
            id_token = response.json().get("idToken")
            print(f"✅ IDトークン取得成功: {id_token[:20]}...")
            
            # 3️⃣ ファンダメンタルデータ取得
            print("\n3️⃣ ファンダメンタルデータ取得中...")
            code = "7203"  # トヨタ自動車
            
            url = f"{BASE_URL}/fundamental"
            params = {
                "code": code
            }
            auth_headers = {
                "Authorization": f"Bearer {id_token}"
            }
            
            response = requests.get(url, headers=auth_headers, params=params)
            print(f"  ステータスコード: {response.status_code}")
            print(f"  レスポンス: {response.text[:500]}")
            
            if response.status_code == 200:
                print(f"✅ {code} のファンダメンタルデータ取得成功")
            else:
                print(f"❌ ファンダメンタルデータ取得失敗")
        else:
            print("❌ IDトークン取得失敗")
    else:
        print("❌ リフレッシュトークン取得失敗")
        
except requests.exceptions.RequestException as e:
    print(f"❌ 通信エラー: {e}")

print("\n" + "=" * 60)
print("🏁 テスト完了")
print("=" * 60)