# check_insert.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

keywords = [
    'st.dataframe',
    'バックテスト',
    'display_codes',
    'bt_columns',
    'チェック',
    'checkbox',
]

for i, line in enumerate(lines, 1):
    for kw in keywords:
        if kw in line:
            print(f"行{i:4d}: {line.rstrip()}")
            break