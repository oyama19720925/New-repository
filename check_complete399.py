# check_complete399.py
with open('app_complete.py', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8', errors='replace')
lines = text.split('\n')

print(f"総行数: {len(lines)}")

# 問題のある行を全て検索
print("\n=== クォートが閉じられていない可能性のある行 ===")
for i, line in enumerate(lines, 1):
    # シングルクォートの数が奇数の行を探す
    stripped = line.strip()
    if stripped.startswith('elif') or stripped.startswith('if'):
        quote_count = line.count("'")
        if quote_count % 2 != 0:
            print(f"Line {i} (quotes={quote_count}): {repr(line)}")

print("\n=== 395〜410行目 ===")
for i in range(394, min(410, len(lines))):
    print(f"Line {i+1}: {repr(lines[i])}")

print("\n=== バイト列確認 (line 399) ===")
raw_lines = raw.split(b'\n')
if len(raw_lines) > 398:
    print(f"Line 399 hex: {raw_lines[398].hex()}")
    print(f"Line 399 raw: {raw_lines[398]}")