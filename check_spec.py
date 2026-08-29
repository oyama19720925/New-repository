# check_spec.py
import requests

# 新しい仕様を確認
url = "https://jpx-jquants.com/spec/"
print(f"🔍 API仕様を確認中: {url}")
print("=" * 60)

try:
    response = requests.get(url)
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス内容:")
    print(response.text[:2000])  # 最初の2000文字を表示
    print("=" * 60)
    
    # エンドポイント情報を抽出
    import re
    endpoints = re.findall(r'https?://[^\s"<>]+', response.text)
    print(f"\n🔗 見つかったURL:")
    for ep in endpoints[:10]:
        print(f"  - {ep}")
        
except Exception as e:
    print(f"❌ エラー: {e}")