with open('app.py', 'rb') as f:
    raw = f.read()

result = bytearray()
i = 0
fix_count = 0

while i < len(raw):
    b1 = raw[i]
    
    # 3バイトUTF-8の先頭かチェック
    if (0xE0 <= b1 <= 0xEF) and (i + 2 < len(raw)):
        b2 = raw[i+1]
        b3 = raw[i+2]
        
        # 2バイト目が正常 かつ 3バイト目が E(0x45)
        if (0x80 <= b2 <= 0xBF) and (b3 == 0x45):
            # Eを削除（b1とb2だけ追加し、Eはスキップ）
            result.append(b1)
            result.append(b2)
            fix_count += 1
            i += 3  # E(0x45)を飛ばす
            continue
    
    result.append(b1)
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
    # 修復された文字列を表示
    print('\n=== 修復後の該当行 ===')
    for line in content.split('\n'):
        if 'ページ' in line or 'CSV' in line or 'マージ' in line:
            print(repr(line[:80]))
except Exception as e:
    print(f'❌ まだエラーがあります: {e}')