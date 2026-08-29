# fix_final2.py

with open('app_complete2.py', 'rb') as f:
    raw = f.read()

# 改行統一
raw = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')

# ===== バイト列レベルで直接修正 =====

replacements = [
    # ① ゴールチEクロス → ゴールデンクロス
    # e38381 45 → e38387 (チE→デ)
    (b'\xe3\x83\xbc\xe3\x83\x81E\xe3\x82\xaf',
     b'\xe3\x83\xbc\xe3\x83\x87\xe3\x83\xb3\xe3\x82\xaf'),

    # ② '銘柄コーチE: → '銘柄コード':
    # e383bce38381 45 3a → e383bce38389 27 3a
    (b'\xe3\x82\xb3\xe3\x83\xbc\xe3\x83\x81E:',
     b'\xe3\x82\xb3\xe3\x83\xbc\xe3\x83\x89\':'),

    # ③ '銘柄名E: → '銘柄名':
    # e5908145 3a → e59081 27 3a
    (b'\xe5\x90\x81E:',
     b'\xe5\x90\x81\':'),

    # ④ '日付E: → '日付':
    # e4bb8145 3a → e4bb81 27 3a
    (b'\xe4\xbb\x81E:',
     b'\xe4\xbb\x81\':'),

    # ⑤ '短期MA > 長期MA: → '短期MA > 長期MA':
    (b"'\xe7\x9f\xad\xe6\x9c\x9fMA > \xe9\x95\xb7\xe6\x9c\x9fMA:",
     b"'\xe7\x9f\xad\xe6\x9c\x9fMA > \xe9\x95\xb7\xe6\x9c\x9fMA':"),

    # ⑥ '短期MA < 長期MA: → '短期MA < 長期MA':
    (b"'\xe7\x9f\xad\xe6\x9c\x9fMA < \xe9\x95\xb7\xe6\x9c\x9fMA:",
     b"'\xe7\x9f\xad\xe6\x9c\x9fMA < \xe9\x95\xb7\xe6\x9c\x9fMA':"),
]

fixes = 0
for old, new in replacements:
    count = raw.count(old)
    if count > 0:
        print(f"✅ {count}箇所修正: {old!r}")
        print(f"        → {new!r}")
        raw = raw.replace(old, new)
        fixes += count
    else:
        print(f"⚠️  見つからず: {old!r}")

# UTF-8デコード確認
try:
    text = raw.decode('utf-8')
    print(f"\n✅ UTF-8デコード成功")
except Exception as e:
    print(f"\n❌ デコードエラー: {e}")
    # エラー位置周辺を表示
    for i in range(len(raw)-1):
        try:
            raw[:i+1].decode('utf-8')
        except:
            print(f"  問題バイト位置: {i}, hex: {raw[i:i+4].hex()}")
            break
    exit()

# 構文チェック
import ast
try:
    ast.parse(text)
    print("✅ 構文チェック成功！")
except SyntaxError as e:
    print(f"❌ 構文エラー: {e}")
    # エラー行周辺表示
    lines = text.split('\n')
    err_line = e.lineno
    print(f"\n=== Line {err_line-2}〜{err_line+2} ===")
    for i in range(max(0, err_line-3), min(len(lines), err_line+2)):
        print(f"  {i+1}: {repr(lines[i])}")

# 保存
with open('app_final2.py', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"\n✅ 合計 {fixes} 箇所修正")
print("✅ app_final2.py として保存しました")
print("次のコマンドで起動してください:")
print("  streamlit run app_final2.py")