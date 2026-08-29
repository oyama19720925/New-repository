with open("C:/stock_system/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=== 640〜710行目 ===")
for j in range(639, min(710, len(lines))):
    print(str(j+1) + ": " + lines[j], end="")