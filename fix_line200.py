# fix_line200.py
import re

with open('app.py', 'rb') as f:
    content = f.read()

# CP932として読み直す
try:
    text = content.decode('cp932')
    print("✅ CP932でデコード成功")
except Exception as e:
    print(f"❌ CP932デコード失敗: {e}")
    try:
        text = content.decode('utf-8', errors='replace')
        print("✅ UTF-8(replace)でデコード成功")
    except Exception as e2:
        print(f"❌ UTF-8デコードも失敗: {e2}")
        exit()

# 修正対象の文字列パターンを置換
replacements = [
    ('短朁E> 長朁E', '短期MA > 長期MA'),
    ('短朁E< 長朁E', '短期MA < 長期MA'),
    ('短朁E', '短期MA'),
    ('長朁E', '長期MA'),
    ('朁E', 'MA'),
]

fixed = text
for old, new in replacements:
    count = fixed.count(old)
    if count > 0:
        fixed = fixed.replace(old, new)
        print(f"✅ '{old}' → '{new}' : {count}箇所修正")

# UTF-8で保存
with open('app_fixed.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

print("\n✅ app_fixed.py として保存しました")
print("次のコマンドで起動してください:")
print("  streamlit run app_fixed.py")