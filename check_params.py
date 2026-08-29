# check_params.py
path = r"C:\stock_system\app.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

keywords = ["mktcap", "MktCap", "vol_min", "AdjVo", "mktcap_min", "時価総額"]
print("=== MktCap/時価総額 関連行 ===")
for i, line in enumerate(lines, 1):
    if any(k.lower() in line.lower() for k in keywords):
        print(f"L{i:4d}: {line}", end="")

print("\n=== スクリーニング条件部分 (latest[) ===")
for i, line in enumerate(lines, 1):
    if "latest[" in line or "result" in line.lower() and "df" in line.lower():
        print(f"L{i:4d}: {line}", end="")