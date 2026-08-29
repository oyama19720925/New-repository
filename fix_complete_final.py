# fix_complete_final.py
# 全ての壊れパターンを辞書で一括置換 → 構文チェック → 保存

import ast

INPUT  = 'app_complete2.py'   # 元の壊れたファイル（修正前）
OUTPUT = 'app_final_clean.py'

# ===== 修正パターン辞書（壊れた文字列 → 正しい文字列）=====
FIX_MAP = {
    # 辞書キー・ラベル系
    '銘柄コーチE':          '銘柄コード',
    '銘柄吁E':              '銘柄名',
    '日仁E':                '日付',
    # スクリーニング条件
    'ゴールチEクロス':      'ゴールデンクロス',
    '短期MA > 長期MA:':     '短期MA > 長期MA\':',   # クォート修正も含む
    '短期MA < 長期MA:':     '短期MA < 長期MA\':',   # クォート修正も含む
    # ボタン・ラベル
    'スクリーニング実衁E':  'スクリーニング実行',
    '実衁E':                '実行',
    'ダウンローチE':        'ダウンロード',
    '条件なし！E':          '条件なし！',
    # チャート
    '出来髁E':              '出来高',
    'ストキャスチEクス':    'ストキャスティクス',
    # selectbox内のクォート修正
    "短期MA > 長期MA, ":    "短期MA > 長期MA', ",
    "短期MA < 長期MA]":     "短期MA < 長期MA']",
    # ボタン文字列の閉じクォート修正
    '"🔍 スクリーニング実行, type=':  '"🔍 スクリーニング実行", type=',
    '"📋 全銘柄表示E条件なし！E':     '"📋 全銘柄表示（条件なし！）',
    '"💾 結果をCSVダウンローチE,':    '"💾 結果をCSVダウンロード",',
    '"💾 全銘柄CSVダウンローチE,':    '"💾 全銘柄CSVダウンロード",',
    '"出来髁E,':                       '"出来高",',
    '"出来髁E,':                       '"出来高",',  # ダブルクォート版
    # subplot_titles
    '"出来髁E, "RSI':                  '"出来高", "RSI',
    '"RSI / ストキャスチEクス"':       '"RSI / ストキャスティクス"',
}

print("=" * 60)
print("STEP 1: ファイル読み込み")
print("=" * 60)

with open(INPUT, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"✅ 読み込み完了: {len(text.splitlines())} 行")

# ===== 一括置換 =====
print("\n" + "=" * 60)
print("STEP 2: パターン一括置換")
print("=" * 60)

fix_count = 0
for broken, correct in FIX_MAP.items():
    count = text.count(broken)
    if count > 0:
        text = text.replace(broken, correct)
        print(f"  ✅ '{broken}' → '{correct}' ({count}箇所)")
        fix_count += count
    
print(f"\n修正箇所合計: {fix_count} 件")

# ===== 構文チェック（繰り返し）=====
print("\n" + "=" * 60)
print("STEP 3: Python構文チェック")
print("=" * 60)

lines = text.split('\n')
max_iter = 30
remaining_errors = 0

for iteration in range(max_iter):
    try:
        ast.parse(text)
        print(f"✅ 構文チェック成功！（{iteration}回追加修正）")
        break
    except SyntaxError as e:
        lineno = e.lineno
        err_line = lines[lineno - 1]
        
        print(f"  [{iteration+1}] Line {lineno}: {e.msg}")
        print(f"       {repr(err_line)}")
        
        # クォートカウント（エスケープを除く）
        sq = err_line.count("'") - err_line.count("\\'")
        dq = err_line.count('"')  - err_line.count('\\"')
        
        fixed = False
        
        # シングルクォートが奇数 → コロンの前に閉じクォートを補完
        if sq % 2 == 1:
            # ':  または ':  のパターンを修正
            import re
            # 末尾が ': で終わっているか確認
            new_line = re.sub(r"'([^':]+):\s*$", r"'\1':", err_line.rstrip())
            if new_line != err_line.rstrip():
                lines[lineno - 1] = new_line + '\n'
                text = '\n'.join(lines)
                print(f"       → コロン前クォート補完")
                fix_count += 1
                fixed = True
            else:
                # 単純に末尾に追加
                new_line = err_line.rstrip('\n\r') + "'"
                lines[lineno - 1] = new_line + '\n'
                text = '\n'.join(lines)
                print(f"       → 末尾シングルクォート補完")
                fix_count += 1
                fixed = True
        
        elif dq % 2 == 1:
            new_line = err_line.rstrip('\n\r') + '"'
            lines[lineno - 1] = new_line + '\n'
            text = '\n'.join(lines)
            print(f"       → 末尾ダブルクォート補完")
            fix_count += 1
            fixed = True
        
        if not fixed:
            print(f"  ⚠️  Line {lineno} は自動修正不可。手動確認が必要です。")
            remaining_errors += 1
            break
else:
    print(f"⚠️  {max_iter}回試行後も構文エラーが残っています")

# ===== 保存 =====
print("\n" + "=" * 60)
print("STEP 4: 保存")
print("=" * 60)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"✅ {OUTPUT} 保存完了")
print(f"✅ 合計 {fix_count} 箇所を修正")

if remaining_errors == 0:
    print(f"\n{'='*60}")
    print(f"🎉 全エラー修正完了！")
    print(f"{'='*60}")
    print(f"\n起動コマンド:")
    print(f"  streamlit run {OUTPUT}")
else:
    print(f"\n⚠️  {remaining_errors}箇所が未修正です。app_final_clean.py を確認してください。")