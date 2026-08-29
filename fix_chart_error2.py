# fix_chart_error2.py

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 「result_df」を使っている行を全て表示
print("=== result_df が登場する行 ===")
for i, line in enumerate(lines, 1):
    if "result_df" in line:
        print(f"行{i:4d}: {line}", end="")