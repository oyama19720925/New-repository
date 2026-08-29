# fix_complete.py
import re

# app.pyをバイナリで読み込む
with open('app.py', 'rb') as f:
    raw = f.read()

# UTF-8でデコード（エラー箇所は置換文字に）
text = raw.decode('utf-8', errors='replace')

print(f"総文字数: {len(text)}")
print(f"置換文字(\\ufffd)の数: {text.count(chr(0xfffd))}")

# 全ての壊れたパターンを修正
replacements = [
    # MAの文字化けパターン
    ('短朁E> 長朁E', '短期MA > 長期MA'),
    ('短朁E< 長朁E', '短期MA < 長期MA'),
    ('短朁E> 長朁E', '短期MA > 長期MA'),  # 別パターン
    ('短朁E< 長朁E', '短期MA < 長期MA'),  # 別パターン
    ('短朁E', '短期MA'),
    ('長朁E', '長期MA'),
    ('朁E', 'MA'),
    # クォートが壊れているパターン（置換文字を含む）
    (f'短期MA > 長期MA{chr(0xfffd)}', "短期MA > 長期MA'"),
    (f'短期MA < 長期MA{chr(0xfffd)}', "短期MA < 長期MA'"),
    (f'短期MA > 長期MA', "短期MA > 長期MA"),
    (f'短期MA < 長期MA', "短期MA < 長期MA"),
    # 置換文字が閉じクォートの代わりになっているケース
    (f"'短期MA > 長期MA{chr(0xfffd)}", "'短期MA > 長期MA'"),
    (f"'短期MA < 長期MA{chr(0xfffd)}", "'短期MA < 長期MA'"),
]

fixed = text
total_fixes = 0
for old, new in replacements:
    count = fixed.count(old)
    if count > 0:
        fixed = fixed.replace(old, new)
        print(f"✅ '{old}' → '{new}' : {count}箇所修正")
        total_fixes += count

# 残っている置換文字を確認
remaining = fixed.count(chr(0xfffd))
print(f"\n残存する置換文字数: {remaining}")

# 置換文字が残っている行を表示
lines = fixed.split('\n')
for i, line in enumerate(lines, 1):
    if chr(0xfffd) in line:
        print(f"  Line {i}: {repr(line)}")

# UTF-8で保存
with open('app_complete.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

print(f"\n✅ 合計 {total_fixes} 箇所修正")
print("✅ app_complete.py として保存しました")
print("次のコマンドで起動してください:")
print("  streamlit run app_complete.py")