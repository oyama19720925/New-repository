with open('app.py', 'rb') as f:
    raw = f.read()

# \xe3\x81E → \xe3\x81\x8b などの修復
# E (0x45) が3バイトUTF-8の3バイト目に入り込んでいるパターンを修復

import re

# パターン: 0xE3 0x8x/0x9x 0x45(E) → 本来は 0xE3 0x8x/0x9x 0x??(正しい3バイト目)
# まず壊れたパターンを全て見つける

result = bytearray()
i = 0
fix_count = 0

while i < len(raw):
    b = raw[i]
    
    # 3バイトUTF-8の開始 (0xE0-0xEF)
    if 0xE0 <= b <= 0xEF and i + 2 < len(raw):
        b2 = raw[i+1]
        b3 = raw[i+2]
        
        # 2バイト目が正常 (0x80-0xBF) かつ 3バイト目が 0x45 (E)
        if 0x80 <= b2 <= 0xBF and b3 == 0x45:
            # Eの次のバイトを3バイト目として使う
            if i + 3 < len(raw):
                b3_real = raw[i+3]
                if 0x80 <= b3_real <= 0xBF:
                    result.append(b)
                    result.append(b2)
                    result.append(b3_real)
                    fix_count += 1
                    i += 4
                    continue
        
        # 正常な3バイト文字
        if 0x80 <= b2 <= 0xBF and 0x80 <= b3 <= 0xBF:
            result.append(b)
            result.append(b2)
            result.append(b3)
            i += 3
            continue
    
    result.append(b)
    i += 1

print(f'修復箇所: {fix_count}件')

with open('app_repaired.py', 'wb') as f:
    f.write(bytes(result))

print('✅ app_repaired.py として保存しました')

# 確認
try:
    with open('app_repaired.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print('✅ UTF-8として正常に読み込めました！')
except Exception as e:
    print(f'❌ まだエラーがあります: {e}')