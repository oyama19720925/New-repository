# C:\stock_system\test_spec.py
import requests
from bs4 import BeautifulSoup

url = "https://jpx-jquants.com/spec/"
r = requests.get(url, timeout=10)

print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print()

# テキスト部分だけ抽出
try:
    soup = BeautifulSoup(r.text, "html.parser")
    
    # スクリプトとスタイルを除去
    for tag in soup(["script", "style"]):
        tag.decompose()
    
    text = soup.get_text(separator="\n")
    # 空行を削除
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    print("\n".join(lines[:100]))  # 最初の100行
except Exception as e:
    print(f"BeautifulSoup未インストール: {e}")
    # 生HTML
    print(r.text[:3000])