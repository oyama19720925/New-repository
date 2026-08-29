import shutil, ast

filepath = r"C:\stock_system\app.py"
shutil.copy(filepath, filepath + ".bak3")
print("✅ バックアップ: app.py.bak3")

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 688~750行目付近を表示して全体像を確認
print("\n=== 685~758行目（全体確認）===")
for i, line in enumerate(lines[684:], start=685):
    print(f"{i:4d}|{repr(line[:100])}")