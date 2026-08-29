# test_cognito_auth.py
import requests
import json
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import hmac
import hashlib
import base64
import datetime

print("🔍 J-Quants API 新しい認証テスト")
print("=" * 60)

# 認証情報
email = "oyama@miomio.jp"
password = "347447498885Mm"
client_id = "56qqt71bs6sdum9pgbkte7feti"
user_pool_id = "ap-northeast-1_FKegKNoTe"

# 1. Cognitoの認証エンドポイント
cognito_url = f"https://cognito-idp.ap-northeast-1.amazonaws.com/"

# CognitoのInitiateAuthリクエスト
auth_data = {
    "AuthFlow": "USER_PASSWORD_AUTH",
    "ClientId": client_id,
    "AuthParameters": {
        "USERNAME": email,
        "PASSWORD": password
    }
}

headers = {
    "Content-Type": "application/x-amz-json-1.1",
    "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"
}

print("\n1️⃣ Cognito認証を試行中...")
try:
    response = requests.post(cognito_url, json=auth_data, headers=headers, timeout=10)
    print(f"   ステータス: {response.status_code}")
    
    if response.status_code == 200:
        auth_result = response.json()
        print(f"   ✅ 認証成功！")
        print(f"   レスポンス: {json.dumps(auth_result, indent=2, ensure_ascii=False)[:500]}")
        
        if 'AuthenticationResult' in auth_result:
            access_token = auth_result['AuthenticationResult']['AccessToken']
            id_token = auth_result['AuthenticationResult']['IdToken']
            refresh_token = auth_result['AuthenticationResult']['RefreshToken']
            
            print(f"\n   🔑 アクセストークン: {access_token[:50]}...")
            print(f"   🔑 IDトークン: {id_token[:50]}...")
            print(f"   🔑 リフレッシュトークン: {refresh_token[:50]}...")
            
            # 2. J-Quants APIをテスト
            print("\n\n2️⃣ J-Quants APIをテスト中...")
            
            # 財務データを取得
            api_url = "https://api.jquants.com/v2/fins/statements"
            api_headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(api_url, headers=api_headers, timeout=10)
            print(f"   ステータス: {response.status_code}")
            print(f"   レスポンス: {response.text[:500]}")
            
    else:
        print(f"   ❌ 認証失敗: {response.text}")
        
except Exception as e:
    print(f"   ❌ エラー: {e}")

print("\n" + "=" * 60)
print("🏁 テスト完了")