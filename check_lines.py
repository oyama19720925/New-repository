# check_lines.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 1190〜1230行 ===")
for i, line in enumerate(lines[1189:1230], start=1190):
    print(f"{i}: {line}", end='')

print("\n\n=== filtered_df が定義されている全行 ===")
for i, line in enumerate(lines, start=1):
    if 'filtered_df' in line and '=' in line and '==' not in line and 'def ' not in line:
        print(f"{i}: {line}", end='')

print("\n\n=== バックテスト結果表示関連の行 ===")
for i, line in enumerate(lines, start=1):
    if any(p in line for p in ['st.dataframe', 'st.write', 'result_df', 'backtest', 'バックテスト']):
        print(f"{i}: {line}", end='')