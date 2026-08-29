# check_apppy.py - app.pyの問題箇所を確認（streamlit不要）
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 690-720行目 ===")
for i, line in enumerate(lines[689:720], start=690):
    print(f"{i:4d}: {repr(line)}")

print("\n=== filtered_df の定義箇所 ===")
for i, line in enumerate(lines, start=1):
    if 'filtered_df' in line:
        print(f"{i:4d}: {line.rstrip()}")

print("\n=== tab_funda の箇所 ===")
for i, line in enumerate(lines, start=1):
    if 'tab_funda' in line:
        print(f"{i:4d}: {line.rstrip()}")