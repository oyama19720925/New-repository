with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 修正マッピング (行番号: 正しい内容)
fixes = {
    9:  '# ========== ページ設定 ==========\n',
    62: '    st.error(f"❌ 必要な列が見つかりません: {missing_cols}")\n',
    67: 'st.sidebar.header("🔧 フィルタ設定")\n',
    80: '    selected_markets = st.sidebar.multiselect("市場を選択（未選択=全て）", markets)\n',
    88: '    selected_sectors = st.sidebar.multiselect("業種を選択（未選択=全て）", sectors)\n',
}

for lineno, new_content in fixes.items():
    print(f"修正前 line {lineno}: {repr(lines[lineno-1])}")
    lines[lineno-1] = new_content
    print(f"修正後 line {lineno}: {repr(lines[lineno-1])}")
    print()

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ app.py を修正・保存しました！")