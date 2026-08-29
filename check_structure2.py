with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 行274以降 ===")
for i, line in enumerate(lines[273:], 274):
    print(f"行{i:4d}: {line}", end='')