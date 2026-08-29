# fix_line283.py
INPUT  = 'app_final_clean3.py'
OUTPUT = 'app_final_clean4.py'

with open(INPUT, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=" * 60)
print("修正前の280-290行目:")
print("=" * 60)
for i in range(279, min(291, len(lines))):
    print(f"  {i+1:3d}: {repr(lines[i])}")

import re
import ast

fix_count = 0

patterns = [
    # Line 283: 全銘柄表示E条件なし！ → 全銘柄表示（条件なし）"
    (
        r'"📋 全銘柄表示E条件なし！, use_container_width',
        '"📋 全銘柄表示（条件なし）", use_container_width'
    ),
    # 念のため他の 表示E パターンも
    (
        r'表示E条件',
        '表示（条件'
    ),
    # 実行Eタン → 実行ボタン (残存確認)
    (
        r'実行Eタン',
        '実行ボタン'
    ),
    # 全銘柄表示E → 全銘柄表示（ (汎用)
    (
        r'全銘柄表示E',
        '全銘柄表示（'
    ),
    # 条件なし！, → 条件なし）", (閉じ括弧と閉じクォートが消えているパターン)
    (
        r'条件なし！, use_container_width=True\)',
        '条件なし）", use_container_width=True)'
    ),
]

for i, line in enumerate(lines):
    original = line
    for pat, rep in patterns:
        if re.search(pat, line):
            new_line = re.sub(pat, rep, line)
            print(f"  ✅ Line {i+1}: {repr(line.rstrip())}")
            print(f"         → {repr(new_line.rstrip())}")
            lines[i] = new_line
            line = new_line
            fix_count += 1

print(f"\n修正箇所: {fix_count} 件")

# ===== 修正後確認 =====
print("\n" + "=" * 60)
print("修正後の280-290行目:")
print("=" * 60)
for i in range(279, min(291, len(lines))):
    print(f"  {i+1:3d}: {repr(lines[i])}")

# ===== 全体構文チェック =====
print("\n" + "=" * 60)
print("構文チェック:")
print("=" * 60)
text = ''.join(lines)
try:
    ast.parse(text)
    print("✅ 構文チェック: OK！エラーなし")
    ok = True
except SyntaxError as e:
    print(f"❌ 構文エラー残存: Line {e.lineno}: {e.msg}")
    err_lines = text.split('\n')
    start = max(0, e.lineno - 4)
    end   = min(len(err_lines), e.lineno + 4)
    for j in range(start, end):
        marker = " >>>>" if j == e.lineno - 1 else "     "
        print(f"  {marker} {j+1:3d}: {repr(err_lines[j])}")
    ok = False

# ===== 保存 =====
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"\n✅ {OUTPUT} 保存完了")

if ok:
    print(f"\n{'='*60}")
    print(f"🎉 全エラー修正完了！")
    print(f"{'='*60}")
    print(f"\n次のコマンドで起動できます:")
    print(f"  copy {OUTPUT} app.py")
    print(f"  streamlit run app.py")
else:
    print(f"\n⚠️  まだエラーが残っています。結果を貼り付けてください。")