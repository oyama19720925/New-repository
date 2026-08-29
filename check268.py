with open('app_final.py', 'rb') as f:
    raw = f.read()

lines = raw.split(b'\n')
print(f"総行数: {len(lines)}")

print("\n=== 263〜275行目 (raw bytes) ===")
for i in range(262, min(275, len(lines))):
    print(f"Line {i+1} hex: {lines[i].hex()}")
    print(f"Line {i+1} raw: {lines[i]}")
    print()