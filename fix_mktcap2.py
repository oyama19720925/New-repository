# fix_mktcap2.py
path = r"C:\stock_system\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# L529: * 1e6 を削除、L137: / 1e6 も削除（既に百万円単位）
old = '"mktcap_min":     mktcap_min * 1e6,'
new = '"mktcap_min":     mktcap_min,'

old2 = '"MktCap(百万)": round(row.get("MktCap", 0) / 1e6, 0),'
new2 = '"MktCap(百万)": round(row.get("MktCap", 0), 0),'

c1 = old in content
c2 = old2 in content

content = content.replace(old, new)
content = content.replace(old2, new2)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"L529修正: {'✅' if c1 else '❌ 見つからず'}")
print(f"L137修正: {'✅' if c2 else '❌ 見つからず'}")
print("完了")