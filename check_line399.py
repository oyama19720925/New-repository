# check_line399.py
with open('app.py', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8', errors='replace')
lines = text.split('\n')

# 395行目〜405行目を表示
print("=== app.py の395〜405行目 ===")
for i in range(394, min(405, len(lines))):
    print(f"Line {i+1}: {repr(lines[i])}")

print("\n=== バイト列確認 (line 399付近) ===")
# 行ごとのバイト位置を計算
raw_lines = raw.split(b'\n')
for i in range(394, min(405, len(raw_lines))):
    print(f"Line {i+1} bytes: {raw_lines[i][:80].hex()}")
    print(f"Line {i+1} text:  {raw_lines[i][:80]}")