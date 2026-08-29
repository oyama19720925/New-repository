with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print("=== 現在の line 14〜20 ===")
for i, line in enumerate(lines[13:20], start=14):
    print(f"{i}: {repr(line)}")