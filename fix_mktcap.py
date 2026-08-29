# fix_mktcap.py
path = r"C:\stock_system\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

fixes = [
    # MktCap フィルタの単位修正（百万円単位に合わせる）
    # 1000億円 = 100,000百万円
    ("mktcap_min = 1_000 * 1e6", "mktcap_min = 100_000"),
    ("mktcap_min = 1000 * 1e6",  "mktcap_min = 100_000"),
    ("mktcap_min = 1e9",          "mktcap_min = 1_000"),
    ("mktcap_min = 10e9",         "mktcap_min = 10_000"),
    # フィルタ条件の比較部分
    ('latest[latest["MktCap"] >= params["mktcap_min"] * 1e6]',
     'latest[latest["MktCap"] >= params["mktcap_min"]]'),
]

changed = []
for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        changed.append(f"✅ '{old}' → '{new}'")

if changed:
    for c in changed: print(c)
else:
    print("⚠️ 自動修正対象が見つかりません")
    print("手動確認が必要です")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("\n✅ app.py 保存完了")