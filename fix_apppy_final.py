with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 修正マッピング
fixes = {
    16: '    st.error("❌ CSVファイルが見つかりません。stock_systemフォルダにCSVを置いてください。")\n',
    19: '    selected_csv = st.sidebar.selectbox("📂 CSVファイルを選択", csv_files)\n',
}

for lineno, new_content in fixes.items():
    print(f"修正前 line {lineno}: {repr(lines[lineno-1])}")
    lines[lineno-1] = new_content
    print(f"修正後 line {lineno}: {repr(lines[lineno-1])}")
    print()

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ app.py を修正・保存しました！")