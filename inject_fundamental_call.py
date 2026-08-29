# C:\stock_system\inject_fundamental_call.py

path = r"C:\stock_system\app.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# app.py 内でバックテスト結果を表示している箇所を探す
keywords = [
    "st.subheader",
    "backtest",
    "バックテスト",
    "screening",
    "スクリーニング",
    "show_fundamental",
    "selected_code",
    "current_price",
]

print("=== キーワード検索結果 ===")
for i, line in enumerate(lines, 1):
    for kw in keywords:
        if kw.lower() in line.lower():
            print(f"L{i:04d}: {line.rstrip()}")
            break