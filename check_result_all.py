# check_result_all.py

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}\n")

print("=== result_df が登場する全行 ===")
for i, line in enumerate(lines, 1):
    if "result_df" in line:
        print(f"行{i:4d}: {line}", end="")

print("\n\n=== session_state が登場する全行 ===")
for i, line in enumerate(lines, 1):
    if "session_state" in line:
        print(f"行{i:4d}: {line}", end="")