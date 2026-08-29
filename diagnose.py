with open(r"C:\stock_system\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 688~710行目 ===")
for i, line in enumerate(lines[687:710], start=688):
    visible = line.replace('\t', '[TAB]').rstrip('\n')
    print(f"{i:4d}|{repr(line[:60])}")