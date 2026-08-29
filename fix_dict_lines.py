# fix_dict_lines.py
# 辞書リテラルの壊れた行を完全修正

INPUT  = 'app_final_clean2.py'
OUTPUT = 'app_final_clean3.py'

with open(INPUT, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=" * 60)
print("修正前の265-275行目:")
print("=" * 60)
for i in range(264, min(275, len(lines))):
    print(f"  {i+1:3d}: {repr(lines[i])}")

fix_count = 0

# 修正対象パターンを定義
# パターン: '銘柄コード': code,' → '銘柄コード': code,
# パターン: '銘柄名':     name,  (空行の次にある場合も含む)

import re

i = 0
while i < len(lines):
    line = lines[i]

    # ケース1: '銘柄コード': code,' (末尾の余分な ' を除去)
    if re.search(r"'銘柄コード':\s+\w+,'$", line.rstrip()):
        new_line = re.sub(r"'銘柄コード':\s+(\w+),'", r"'銘柄コード': \1,", line.rstrip()) + '\n'
        print(f"  ✅ Line {i+1}: {repr(line.rstrip())} → {repr(new_line.rstrip())}")
        lines[i] = new_line
        fix_count += 1
        # 次行が空行なら削除
        if i+1 < len(lines) and lines[i+1].strip() == '':
            print(f"  ✅ Line {i+2}: 空行を削除")
            lines.pop(i+1)
            fix_count += 1

    # ケース2: 315-325行目付近も同じパターンがある可能性
    # (fix_line268.pyで318-321行目も修正済みだが念のため)
    elif re.search(r"'銘柄コード':\s+\w+,'$", line.rstrip()):
        new_line = re.sub(r"'銘柄コード':\s+(\w+),'", r"'銘柄コード': \1,", line.rstrip()) + '\n'
        print(f"  ✅ Line {i+1}: {repr(line.rstrip())} → {repr(new_line.rstrip())}")
        lines[i] = new_line
        fix_count += 1
        if i+1 < len(lines) and lines[i+1].strip() == '':
            print(f"  ✅ Line {i+2}: 空行を削除")
            lines.pop(i+1)
            fix_count += 1

    # ケース3: '実行Eタン' → '実行ボタン'
    elif '実行Eタン' in line:
        new_line = line.replace('実行Eタン', '実行ボタン')
        print(f"  ✅ Line {i+1}: 実行Eタン → 実行ボタン")
        lines[i] = new_line
        fix_count += 1

    i += 1

print(f"\n修正箇所: {fix_count} 件")

# ===== 修正後確認 =====
print("\n" + "=" * 60)
print("修正後の265-275行目:")
print("=" * 60)
for i in range(264, min(275, len(lines))):
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
    print(f"\n起動コマンド:")
    print(f"  copy {OUTPUT} app.py")
    print(f"  streamlit run app.py")