# fix_fundamental_position.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# ── 1. 1208〜1213行のファンダメンタルブロックを削除 ──────────────────
# (0-indexed: 1207〜1212)
block_start = 1207  # 0-indexed
block_end   = 1214  # 0-indexed (exclusive)

removed = lines[block_start:block_end]
print("=== 削除するブロック ===")
for i, l in enumerate(removed, start=block_start+1):
    print(f"{i}: {l}", end='')

new_lines = lines[:block_start] + lines[block_end:]

# ── 2. render_summary の後にファンダメンタル表示を挿入 ────────────────
# 削除後の行番号を再計算して render_summary を探す
insert_after = None
for i, line in enumerate(new_lines):
    if 'render_summary(summary, color)' in line:
        insert_after = i
        break

if insert_after is None:
    print("❌ render_summary が見つかりません")
    exit(1)

print(f"\n=== 挿入位置: {insert_after+1}行目の後 ===")
print(f"該当行: {new_lines[insert_after]}", end='')

# 挿入するコード（インデントは24スペース = ループ内）
fundamental_block = [
    '\n',
    '                        # ===== ファンダメンタルデータ表示 =====\n',
    "                        if st.session_state.get('show_fundamental', True):\n",
    "                            with st.spinner('ファンダメンタルデータ取得中...'):\n",
    "                                latest_price = float(df_s['Close'].iloc[-1]) \\\n",
    "                                    if 'Close' in df_s.columns and len(df_s) > 0 else None\n",
    '                                fd = get_fundamental_data(code, current_price=latest_price)\n',
    '                                display_fundamental(fd, code, name)\n',
    '\n',
]

new_lines = new_lines[:insert_after+1] + fundamental_block + new_lines[insert_after+1:]

print(f"\n=== 挿入後の確認（挿入位置周辺） ===")
start_check = max(0, insert_after - 1)
end_check   = min(len(new_lines), insert_after + len(fundamental_block) + 3)
for i, line in enumerate(new_lines[start_check:end_check], start=start_check+1):
    print(f"{i}: {line}", end='')

# ── 3. バックアップ＆書き込み ─────────────────────────────────────────
import shutil, datetime
backup = f'app_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
shutil.copy('app.py', backup)
print(f"\n✅ バックアップ作成: {backup}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ app.py を更新しました！")
print(f"   削除: 旧1208〜1213行のファンダブロック")
print(f"   挿入: render_summary の直後（ループ内）")