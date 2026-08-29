# app.py の CSV読み込み部分を修正する

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修正前後を確認
old_code = 'files = glob.glob("*.csv")'
new_code = 'files = ["stocks_OHLC_3months.csv"]  # 最新データを固定指定'

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 修正完了！stocks_OHLC_3months.csv を固定で読み込むように変更しました")
else:
    print("❌ 対象コードが見つかりません")
    print("app.py の行52付近を手動で確認してください")