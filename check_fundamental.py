# check_fundamental.py
path = r"C:\stock_system\app.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

keywords = ["fundamental", "fins", "API_KEY", "get_fundamental", "X-API-KEY"]
for i, line in enumerate(lines, 1):
    if any(k.lower() in line.lower() for k in keywords):
        print(f"L{i:4d}: {line}", end="")