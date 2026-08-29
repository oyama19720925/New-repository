# C:\stock_system\inspect_main_ui.py

path = r"C:\stock_system\app.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
print(f"総行数: {total}")
print()

# L400以降のメインUI部分を表示（スクリーニング結果・バックテスト表示箇所）
print("=== L400〜末尾 ===")
for i, line in enumerate(lines[399:], 400):
    print(f"L{i:04d}: {line.rstrip()}")