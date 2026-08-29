# fix_complete2.py

with open('app_complete.py', 'rb') as f:
    raw = f.read()

# \r\r\n → \r\n に修正
fixed = raw.replace(b'\r\r\n', b'\r\n')
# \r\r → \n に修正（\nが後に続かない場合）
fixed = fixed.replace(b'\r\r', b'\n')
# 念のため \r\n を \n に統一
fixed = fixed.replace(b'\r\n', b'\n')
# 残った単独 \r も \n に
fixed = fixed.replace(b'\r', b'\n')

# デコードテスト
try:
    text = fixed.decode('utf-8')
    print(f"✅ UTF-8デコード成功")
except UnicodeDecodeError as e:
    print(f"❌ デコードエラー: {e}")

# クォートチェック
lines = text.split('\n')
print(f"総行数: {len(lines)}")

print("\n=== クォートが奇数の elif/if 行 ===")
found = False
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith(('elif', 'if')):
        sq = line.count("'")
        dq = line.count('"')
        if sq % 2 != 0 or dq % 2 != 0:
            print(f"Line {i} (sq={sq}, dq={dq}): {repr(line)}")
            found = True
if not found:
    print("  問題なし ✅")

with open('app_complete2.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("\n✅ app_complete2.py として保存しました")
print("次のコマンドで起動してください:")
print("  streamlit run app_complete2.py")