with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=== 行600〜625 確認 ===")
for i, line in enumerate(lines[599:624], 600):
    print(f"行{i:4d}: {line}", end="")