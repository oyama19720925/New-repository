with open('app.py', 'rb') as f:
    raw = f.read()

# UTF-8としてデコードを試みて問題箇所を特定
i = 0
errors = []
while i < len(raw):
    try:
        char_len = 1
        b = raw[i]
        if b >= 0xF0:
            char_len = 4
        elif b >= 0xE0:
            char_len = 3
        elif b >= 0xC0:
            char_len = 2
        raw[i:i+char_len].decode('utf-8')
        i += char_len
    except Exception as e:
        errors.append((i, raw[i:i+4].hex(), e))
        i += 1

if errors:
    print(f'❌ {len(errors)}箇所に問題があります：')
    for pos, hexval, err in errors[:10]:
        # 前後の文脈も表示
        context = raw[max(0,pos-20):pos+20]
        print(f'  位置{pos}: {hexval} → {err}')
        print(f'  前後: {context}')
        print()
else:
    print('✅ UTF-8として正常です')