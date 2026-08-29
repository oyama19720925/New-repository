# fix_fetch_fundamental.py
path = r"C:\stock_system\app.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# fins_summary → data に修正
old = 'items = resp.json().get("fins_summary", [])'
new = 'items = resp.json().get("data", [])'

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 修正完了: fins_summary → data")
else:
    print("❌ 対象文字列が見つかりません")
    # 現在の該当行を確認
    for i, line in enumerate(content.split('\n'), 1):
        if 'fins_summary' in line or 'get("data"' in line:
            print(f"L{i}: {line}")