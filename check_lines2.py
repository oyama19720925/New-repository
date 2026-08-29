# check_lines2.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== 1195〜1230行 ===")
for i, line in enumerate(lines[1194:1230], start=1195):
    print(f"{i}: {line}", end='')

print("\n\n=== filtered_df の全出現箇所 ===")
for i, line in enumerate(lines, start=1):
    if 'filtered_df' in line:
        print(f"{i}: {line}", end='')

print("\n\n=== 1200〜1220行周辺のインデント確認 ===")
for i, line in enumerate(lines[1199:1220], start=1200):
    print(f"{i}|{repr(line)}")