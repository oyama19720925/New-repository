with open('app.py', 'rb') as f:
    raw = f.read()

# Eが混入している箇所を全て表示
print("=== 0x45(E)が3バイト目に混入している箇所 ===")
count = 0
for i in range(len(raw) - 2):
    b1 = raw[i]
    b2 = raw[i+1]
    b3 = raw[i+2]
    
    # 3バイトUTF-8の先頭 + 正常な2バイト目 + E(0x45)
    if 0xE0 <= b1 <= 0xEF and 0x80 <= b2 <= 0xBF and b3 == 0x45:
        print(f"位置{i}: {raw[i:i+6].hex()} | raw: {raw[i:i+6]}")
        count += 1

print(f"\n合計: {count}箇所")

# 位置185の前後20バイトを詳細表示
print("\n=== 位置185の前後20バイト (hex) ===")
print(raw[165:210].hex())
print("\n=== 位置185の前後20バイト (raw) ===")
print(raw[165:210])