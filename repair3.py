with open('app.py', 'rb') as f:
    raw = f.read()

# まず全エラー位置を特定
def find_all_errors(data):
    errors = []
    i = 0
    while i < len(data):
        b = data[i]
        if b < 0x80:
            i += 1
        elif 0xC2 <= b <= 0xDF:
            if i+1 < len(data) and 0x80 <= data[i+1] <= 0xBF:
                i += 2
            else:
                errors.append(i)
                i += 1
        elif 0xE0 <= b <= 0xEF:
            if (i+2 < len(data) and
                0x80 <= data[i+1] <= 0xBF and
                0x80 <= data[i+2] <= 0xBF):
                i += 3
            else:
                errors.append(i)
                i += 1
        elif 0xF0 <= b <= 0xF4:
            if (i+3 < len(data) and
                0x80 <= data[i+1] <= 0xBF and
                0x80 <= data[i+2] <= 0xBF and
                0x80 <= data[i+3] <= 0xBF):
                i += 4
            else:
                errors.append(i)
                i += 1
        else:
            errors.append(i)
            i += 1
    return errors

# エラーバイトを全てスキップして再構築
def rebuild(data):
    errors = set(find_all_errors(data))
    result = bytearray()
    i = 0
    fix_count = 0
    while i < len(data):
        if i in errors:
            fix_count += 1
            i += 1  # 不正バイトをスキップ
        else:
            result.append(data[i])
            i += 1
    return bytes(result), fix_count

# 複数回パスして完全修復
data = raw
total_fixed = 0
for pass_num in range(1, 6):
    errors = find_all_errors(data)
    if not errors:
        print(f"✅ パス{pass_num-1}で完全修復完了！")
        break
    data, fixed = rebuild(data)
    total_fixed += fixed
    print(f"パス{pass_num}: {fixed}件修復、残り{len(find_all_errors(data))}件")

print(f"\n合計修復: {total_fixed}件")

with open('app_repaired.py', 'wb') as f:
    f.write(data)
print("✅ app_repaired.py として保存しました")

# 最終確認
try:
    with open('app_repaired.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print("✅ UTF-8として正常に読み込めました！")
    print(f"総行数: {len(content.splitlines())}行")
except Exception as e:
    print(f"❌ まだエラーがあります: {e}")