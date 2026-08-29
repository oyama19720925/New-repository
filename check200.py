# check200.py
with open('app_complete2.py', 'rb') as f:
    raw = f.read()

lines = raw.split(b'\n')
print(f"総行数: {len(lines)}")

print("\n=== 195〜210行目 (raw bytes) ===")
for i in range(194, min(210, len(lines))):
    print(f"Line {i+1} hex: {lines[i].hex()}")
    print(f"Line {i+1} raw: {lines[i]}")
    print()