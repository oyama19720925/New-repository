# app.py を読み込む
with open('app.py', encoding='utf-8') as f:
    content = f.read()

# 行778の古い呼び方に修正
old = 'trades_df, equity_df = run_backtest(df_s, params, flags, bt_cap)'
new = 'trades_df, equity_df = run_backtest(df_s, bt_short, bt_long, bt_cap)'

if old in content:
    content = content.replace(old, new)
    print("✅ 修正成功：行778を修正しました")
else:
    print("⚠️ 該当箇所が見つかりませんでした")
    print("前後の文字列を確認してください")

# 修正後を保存
with open('app.py', encoding='utf-8', mode='w') as f:
    f.write(content)

print("✅ app.py を保存しました")