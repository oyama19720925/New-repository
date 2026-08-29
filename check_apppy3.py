# check_apppy3.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")

print("\n=== 960-1050行目 ===")
for i, line in enumerate(lines[959:1050], start=960):
    print(f"{i:4d}: {line.rstrip()}")

print("\n=== fetch_fundamental 関数の定義箇所 ===")
for i, line in enumerate(lines, start=1):
    if 'def fetch_fundamental' in line or 'def get_fundamental' in line:
        print(f"{i:4d}: {line.rstrip()}")

print("\n=== エラーになりそうな箇所（filtered_df, NameError等）===")
for i, line in enumerate(lines, start=1):
    if 'filtered_df' in line:
        print(f"{i:4d}: {line.rstrip()}")

print("\n=== 最後の50行 ===")
for i, line in enumerate(lines[-50:], start=len(lines)-49):
    print(f"{i:4d}: {line.rstrip()}")