# check_cognito.py
import requests
import json
import re

print("🔍 J-Quants 新しい認証システムの確認")
print("=" * 60)

# 1. 認証関連のJavaScriptファイルを確認
js_files = [
    "https://jpx-jquants.com/_next/static/chunks/2647-2fe238d31d7a86ac.js",
    "https://jpx-jquants.com/_next/static/chunks/app/layout-d813313b7dfb8c26.js",
    "https://jpx-jquants.com/_next/static/chunks/7150-4f526cc80c4a7c78.js"
]

for js_url in js_files:
    print(f"\n🔍 {js_url.split('/')[-1]} を確認中...")
    try:
        response = requests.get(js_url, timeout=10)
        content = response.text
        
        # Cognito関連の情報を探す
        cognito_patterns = [
            r'userPoolId[":\s]+["\']?[^"\',}]+',
            r'userPoolClientId[":\s]+["\']?[^"\',}]+',
            r'cognito[a-zA-Z0-9._-]*',
            r'oauth2/token',
            r'api\.jquants\.com[^\s"<>]*',
            r'https://[a-zA-Z0-9.-]*cognito[a-zA-Z0-9.-]*'
        ]
        
        for pattern in cognito_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"   パターン '{pattern}':")
                for match in matches[:5]:
                    print(f"     - {match}")
                    
        # エンドポイント情報を探す
        api_patterns = [
            r'https://api\.jquants\.com[^\s"<>]*',
            r'/v2/[a-zA-Z0-9/_-]+',
            r'api\.jquants\.com[^\s"<>]*'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"   APIパターン '{pattern}':")
                for match in matches[:10]:
                    print(f"     - {match}")
                    
    except Exception as e:
        print(f"   ❌ エラー: {e}")

print("\n" + "=" * 60)
print("🏁 確認完了")