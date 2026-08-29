# check_apppy2.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== 720-800行目 ===")
for i, line in enumerate(lines[719:800], start=720):
    print(f"{i:4d}: {line.rstrip()}")

print("\n=== 870-960行目 ===")
for i, line in enumerate(lines[869:960], start=870):
    print(f"{i:4d}: {line.rstrip()}")

print("\n=== スクリーニング結果の変数名を探す ===")
keywords = ['result_df', 'screen_df', 'screened', 'filtered', 'df_result', 'df_screen']
for i, line in enumerate(lines, start=1):
    for kw in keywords:
        if kw in line and '=' in line:
            print(f"{i:4d}: {line.rstrip()}")