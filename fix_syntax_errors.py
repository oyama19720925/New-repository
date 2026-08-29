# fix_syntax_errors.py
# 構文エラー（未閉じ文字列）を全箇所検出・修正

import ast
import re

with open('app_complete2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")

# 修正パターン定義
# キーは「壊れた文字列」、値は「正しい文字列」
fix_patterns = {
    # 閉じクォートが欠落しているパターン
    "== '短期MA > 長期MA:":     "== '短期MA > 長期MA':",
    "== '短期MA < 長期MA:":     "== '短期MA < 長期MA':",
    "== '短期MA > 長期MA'E":    "== '短期MA > 長期MA'",
    "== '短期MA < 長期MA'E":    "== '短期MA < 長期MA'",
    # 末尾Eパターン（辞書キー等）
    "'銘柄コE:":                 "'銘柄コード':",
    "'銘柄名E:":                 "'銘柄名':",
    "'日付E:":                   "'日付':",
    "'銘柄コード'E:":            "'銘柄コード':",
    "'銘柄名'E:":                "'銘柄名':",
    "'日付'E:":                  "'日付':",
    # ボタンラベル等
    'スクリーニング実衁E':       'スクリーニング実行',
    '実衁E':                     '実行',
}

fixed_lines = []
fix_count = 0

for i, line in enumerate(lines, 1):
    original = line
    for broken, correct in fix_patterns.items():
        if broken in line:
            line = line.replace(broken, correct)
            print(f"  ✅ Line {i}: '{broken}' → '{correct}'")
            fix_count += 1
    fixed_lines.append(line)

print(f"\n修正箇所合計: {fix_count} 件")

# 修正後のテキストを結合
fixed_text = ''.join(fixed_lines)

# UTF-8デコード確認
print("\n" + "=" * 60)
print("STEP: Python構文チェック（修正後）")
print("=" * 60)

# 構文エラーを繰り返しチェック
max_iterations = 20
for iteration in range(max_iterations):
    try:
        ast.parse(fixed_text)
        print(f"✅ 構文チェック成功！（{iteration}回修正後）")
        break
    except SyntaxError as e:
        lineno = e.lineno
        print(f"❌ 構文エラー残存: Line {lineno}: {e.msg}")
        
        # エラー行を表示
        err_lines = fixed_text.split('\n')
        for li in range(max(0, lineno-3), min(len(err_lines), lineno+2)):
            print(f"  {li+1}: {repr(err_lines[li])}")
        
        # 自動修正を試みる
        err_line = err_lines[lineno - 1]
        print(f"\n  → 自動修正試行: {repr(err_line)}")
        
        # 未閉じシングルクォートの検出
        sq_count = err_line.count("'") - err_line.count("\\'")
        dq_count = err_line.count('"') - err_line.count('\\"')
        
        if sq_count % 2 == 1:
            # シングルクォートが奇数 → 末尾に追加
            fixed_line = err_line.rstrip('\n\r') + "'\n"
            print(f"  → シングルクォート補完: {repr(fixed_line)}")
            err_lines[lineno - 1] = fixed_line
            fixed_text = '\n'.join(err_lines)
            fix_count += 1
        elif dq_count % 2 == 1:
            # ダブルクォートが奇数 → 末尾に追加
            fixed_line = err_line.rstrip('\n\r') + '"\n'
            print(f"  → ダブルクォート補完: {repr(fixed_line)}")
            err_lines[lineno - 1] = fixed_line
            fixed_text = '\n'.join(err_lines)
            fix_count += 1
        else:
            print(f"  ⚠️ 自動修正できません。手動確認が必要です。")
            break
else:
    print(f"⚠️ {max_iterations}回試行後も構文エラーが残っています")

# 保存
with open('app_fixed_final.py', 'w', encoding='utf-8') as f:
    f.write(fixed_text)

print(f"\n{'='*60}")
print(f"✅ 合計 {fix_count} 箇所を修正")
print(f"✅ app_fixed_final.py として保存完了")
print(f"{'='*60}")
print(f"\n起動コマンド:")
print(f"  streamlit run app_fixed_final.py")