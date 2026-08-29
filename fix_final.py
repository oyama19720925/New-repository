# fix_final.py

with open('app_complete2.py', 'rb') as f:
    raw = f.read()

# \r\n と \r を統一
raw = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')

text = raw.decode('utf-8', errors='replace')
lines = text.split('\n')

fixes = 0

new_lines = []
for i, line in enumerate(lines, 1):
    original = line

    # ① 'ゴールチE クロス' → 'ゴールデンクロス'
    # hex: e382b4e383bce383abe3838145e382afe383ade382b9
    # E (45) が \xe3\x83\x81 の後に混入している
    line = line.replace(
        '\u30b4\u30fc\u30eb\u30c1E\u30af\u30ed\u30b9',
        '\u30b4\u30fc\u30eb\u30c7\u30f3\u30af\u30ed\u30b9'
    )

    # ② '短期MA > 長期MA: → '短期MA > 長期MA'  (閉じクォート追加)
    if "== '\u77ed\u671fMA > \u9577\u671fMA:" in line:
        line = line.replace(
            "== '\u77ed\u671fMA > \u9577\u671fMA:",
            "== '\u77ed\u671fMA > \u9577\u671fMA':"
        )

    # ③ '短期MA < 長期MA: → '短期MA < 長期MA'  (閉じクォート追加)
    if "== '\u77ed\u671fMA < \u9577\u671fMA:" in line:
        line = line.replace(
            "== '\u77ed\u671fMA < \u9577\u671fMA:",
            "== '\u77ed\u671fMA < \u9577\u671fMA':"
        )

    if line != original:
        print(f"✅ Line {i}: {repr(original)}")
        print(f"        → {repr(line)}")
        fixes += 1

    new_lines.append(line)

text_fixed = '\n'.join(new_lines)

# デコード確認
try:
    text_fixed.encode('utf-8')
    print(f"\n✅ UTF-8エンコード成功")
except Exception as e:
    print(f"\n❌ エラー: {e}")

# 構文チェック
import ast
try:
    ast.parse(text_fixed)
    print("✅ 構文チェック成功！")
except SyntaxError as e:
    print(f"❌ 構文エラー: {e}")

with open('app_final.py', 'w', encoding='utf-8') as f:
    f.write(text_fixed)

print(f"\n✅ 合計 {fixes} 箇所修正")
print("✅ app_final.py として保存しました")
print("次のコマンドで起動してください:")
print("  streamlit run app_final.py")