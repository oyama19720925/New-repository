
# check_changes.py
import requests
import re
import json

print("🔍 J-Quants API仕様変更点の確認")
print("=" * 60)

# 1. 仕様ページを取得
url = "https://jpx-jquants.com/spec/"
response = requests.get(url)
html = response.text

# 2. "Endpoint & Parameter Changes" セクションの内容を抽出
print("\n1️⃣ 'Endpoint & Parameter Changes' セクションを検索...")

# HTMLタグを除去してテキストを抽出
text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text)

# セクションを見つける
section_start = text.find('Endpoint & Parameter Changes')
if section_start != -1:
    section_text = text[section_start:section_start+2000]
    print("   セクション内容:")
    print(f"   {section_text}")
else:
    print("   ⚠️ セクションが見つかりません")

# 3. JavaScriptチャンクファイルからAPI情報を抽出
print("\n2️⃣ JavaScriptファイルからAPI情報を抽出...")
js_files = re.findall(r'src="([^"]*\.js[^"]*)"', html)
print(f"   見つかったJSファイル: {len(js_files)}個")

for js_file in js_files:
    if 'chunk' in js_file or 'main' in js_file:
        print(f"\n   🔍 {js_file} を確認中...")
        try:
            # 完全なURLを構築
            if js_file.startswith('/'):
                js_url = f"https://jpx-jquants.com{js_file}"
            else:
                js_url = js_file
            
            js_response = requests.get(js_url, timeout=10)
            if js_response.status_code == 200:
                js_content = js_response.text
                
                # APIエンドポイントを探す
                api_patterns = [
                    r'/v2/[a-zA-Z0-9/_-]+',
                    r'api\.jquants\.com[^\s"<>]*',
                    r'https://api\.jquants\.com[^\s"<>]*'
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, js_content)
                    if matches:
                        print(f"   パターン '{pattern}':")
                        for match in matches[:10]:
                            print(f"     - {match}")
                
                # auth関連のコードを探す
                auth_keywords = ['refresh_token', 'id_token', 'auth', 'token']
                for keyword in auth_keywords:
                    if keyword in js_content:
                        idx = js_content.find(keyword)
                        context = js_content[max(0, idx-100):idx+200]
                        print(f"\n   ✅ '{keyword}' 関連コード:")
                        print(f"   ...{context}...")
                        
        except Exception as e:
            print(f"   ❌ エラー: {e}")

print("\n" + "=" * 60)
print("🏁 確認完了")