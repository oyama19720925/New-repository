# check_fundamental3.py
path = r"C:\stock_system\app.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# API_BASE確認
for i, line in enumerate(lines, 1):
    if "API_BASE" in line:
        print(f"L{i:4d}: {line}", end="")

print("--- L695-720 ---")
for i, line in enumerate(lines, 1):
    if 695 <= i <= 720:
        print(f"L{i:4d}: {line}", end="")