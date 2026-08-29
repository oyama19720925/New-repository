# diagnostic.py - エンドポイント診断
import requests

EMAIL = "oyama@miomio.jp"
PASSWORD = "347447498885Mm"

# 考えられるエンドポイントをすべて試す
endpoints = [
    "https://api.jquants.com/v2/auth/refresh_token",
    "https://api.jquants.com/v2/auth_v2/auth_token",
    "https://api.jquants.com/v2/auth_v2/refresh_token",
    "https://api.jquants.com/v2/auth/auth_token",
    "https://api.jquants.com/v2/auth/refresh_token",
    "https://jquants.com/api/v2/auth/refresh_token",
    "https://api.jquants.co.jp/v2/auth/refresh_token",
    "https://api.jquants.jp/v2/auth/refresh_token"
]

print("🔍 エンドポイント診断開始")
print("=" * 60)

for url in endpoints:
    print(f"\n試行: {url}")
    try:
        payload = {
            "mail": EMAIL,
            "password": PASSWORD
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"  ステータス: {response.status_code}")
        print(f"  レスポンス: {response.text[:200]}")
        
        if response.status_code == 200:
            print(f"  ✅ このエンドポイントが正しい！")
            break
        elif response.status_code == 404:
            print(f"  ❌ エンドポイントが存在しない")
        elif response.status_code == 403:
            print(f"  ❌ アクセス拒否（認証情報が不正）")
        elif response.status_code == 401:
            print(f"  ❌ 認証失敗（認証情報が不正）")
        else:
            print(f"  ⚠️ その他のエラー")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ 通信エラー: {e}")

print("\n" + "=" * 60)
print("🏁 診断完了")