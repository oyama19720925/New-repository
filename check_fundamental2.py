# check_fundamental2.py
path = r"C:\stock_system\app.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# L354周辺を表示
for i, line in enumerate(lines, 1):
    if 350 <= i <= 400:
        print(f"L{i:4d}: {line}", end="")