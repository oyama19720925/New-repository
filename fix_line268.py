# fix_line268.py
# app_final_clean.py の268行目周辺を正確に修正

INPUT  = 'app_final_clean.py'
OUTPUT = 'app_final_clean2.py'

with open(INPUT, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=" * 60)
print("修正前の260-280行目:")
print("=" * 60)
for i in range(259, min(280, len(lines))):
    print(f"  {i+1:3d}: {repr(lines[i])}")

# ===== 修正パターン =====
# 辞書のキー部分でクォートが閉じられていないパターンを修正
import re

fix_count = 0
for i, line in enumerate(lines):
    original = line
    
    # パターン1: '銘柄コード: code, → '銘柄コード': code,
    if re.search(r"'銘柄コード:\s+\w", line):
        line = re.sub(r"'(銘柄コード):\s+", r"'\1': ", line)
        
    # パターン2: '銘柄名:     name, → '銘柄名':     name,
    if re.search(r"'銘柄名:\s+\w", line):
        line = re.sub(r"'(銘柄名):\s+", r"'\1':     ", line)
        
    # パターン3: '日付:       last[ → '日付':       last[
    if re.search(r"'日付:\s+\w", line):
        line = re.sub(r"'(日付):\s+", r"'\1':       ", line)

    # パターン4: '銘柄コード: code,' (末尾にシングルクォートが補完されてしまった行)
    # 例: "                '銘柄コード: code,'\n"  → "                '銘柄コード': code,\n"
    if re.search(r"'銘柄コード: \w+,'", line):
        line = re.sub(r"'銘柄コード: (\w+),'", r"'銘柄コード': \1,", line)

    if line != original:
        print(f"  ✅ Line {i+1}: {repr(original.rstrip())} → {repr(line.rstrip())}")
        fix_count += 1
    lines[i] = line

print(f"\n修正箇所: {fix_count} 件")

print("\n" + "=" * 60)
print("修正後の260-280行目:")
print("=" * 60)
for i in range(259, min(280, len(lines))):
    print(f"  {i+1:3d}: {repr(lines[i])}")

# ===== 構文チェック =====
import ast
text = ''.join(lines)
try:
    ast.parse(text)
    print("\n✅ 構文チェック: OK！")
    ok = True
except SyntaxError as e:
    print(f"\n❌ 構文エラー残存: Line {e.lineno}: {e.msg}")
    # エラー周辺を表示
    err_lines = text.split('\n')
    start = max(0, e.lineno - 3)
    end   = min(len(err_lines), e.lineno + 3)
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
    print(f"\n起動コマンド:")
    print(f"  streamlit run {OUTPUT}")