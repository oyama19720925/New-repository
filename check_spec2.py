# check_spec2.py
import requests
import re
import json

print("🔍 J-Quants API仕様詳細確認ツール")
print("=" * 60)

# 1. ページのHTMLを取得
url = "https://jpx-jquants.com/spec/"
response = requests.get(url)
html = response.text

# 2. JavaScriptファイルやAPIの参照を探す
print("\n1️⃣ JavaScriptファイルを探す...")
js_files = re.findall(r'src="([^"]*\.js[^"]*)"', html)
for js in js_files[:10]:
    print(f"   - {js}")

# 3. JSONデータやAPIエンドポイントを探す
print("\n2️⃣ APIエンドポイントを探す...")
api_patterns = [
    r'/v2/[a-zA-Z0-9/_-]+',
    r'api\.[a-zA-Z0-9.-]+',
    r'https://api\.jquants\.com[^\s"<>]*'
]

for pattern in api_patterns:
    matches = re.findall(pattern, html)
    if matches:
        print(f"   パターン '{pattern}':")
        for match in matches[:10]:
            print(f"     - {match}")

# 4. OpenAPI/Swaggerの仕様を探す
print("\n3️⃣ OpenAPI/Swagger仕様を探す...")
swagger_patterns = [
    r'openapi[^"<>]*\.json',
    r'swagger[^"<>]*\.json',
    r'api-docs[^"<>]*',
    r'spec[^"<>]*\.json'
]

for pattern in swagger_patterns:
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        print(f"   パターン '{pattern}':")
        for match in matches[:5]:
            print(f"     - {match}")

# 5. ページ内のテキストからAPI情報を抽出
print("\n4️⃣ ページ内テキストの検索...")
keywords = ['auth', 'token', 'endpoint', 'refresh', 'fundamental']
text = re.sub(r'<[^>]+>', ' ', html)  # HTMLタグを除去
for keyword in keywords:
    if keyword.lower() in text.lower():
        # キーワードの周辺テキストを表示
        idx = text.lower().find(keyword.lower())
        context = text[max(0, idx-50):idx+100].strip()
        print(f"   ✅ '{keyword}' が見つかりました:")
        print(f"      文脈: ...{context}...")

print("\n" + "=" * 60)
print("🏁 確認完了")