# check_lines3.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== 1080〜1130行（selected_code定義周辺） ===")
for i, line in enumerate(lines[1079:1130], start=1080):
    print(f"{i}: {line}", end='')

print("\n\n=== 1220〜1280行（バックテスト処理周辺） ===")
for i, line in enumerate(lines[1219:1280], start=1220):
    print(f"{i}: {line}", end='')