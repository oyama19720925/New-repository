# check_result_df.py

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== result_df が登場する全行 ===")
for i, line in enumerate(lines, 1):
    if "result_df" in line:
        print(f"行{i:4d}: {line}", end="")

print("\n\n=== 行680〜700の内容 ===")
for i, line in enumerate(lines[679:699], 680):
    print(f"行{i:4d}: {line}", end="")