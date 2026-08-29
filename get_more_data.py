import jquantsapi
import pandas as pd

# APIキーを設定
API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"

cli = jquantsapi.ClientV2(api_key=API_KEY)

print("7月・8月データを取得中...")

df_new = cli.get_eq_bars_daily_range(
    start_dt="20260701",
    end_dt="20260813"
)

print(f"取得完了: {len(df_new):,}行")

# 既存データを読み込み
df_old = pd.read_csv(
    r'C:\stock_system\stocks_OHLC_with_names.csv',
    low_memory=False
)

print(f"既存データ: {len(df_old):,}行")

# ★修正：日付の型を統一（両方とも文字列に変換）
df_old['Date'] = df_old['Date'].astype(str)
df_new['Date'] = df_new['Date'].astype(str)

# 結合
df_combined = pd.concat([df_old, df_new], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=['Date', 'Code'])
df_combined = df_combined.sort_values(['Code', 'Date'])

print(f"結合後: {len(df_combined):,}行")
print(f"期間: {df_combined['Date'].min()} ～ {df_combined['Date'].max()}")
print(f"銘柄数: {df_combined['Code'].nunique():,}")

# 保存
df_combined.to_csv(
    r'C:\stock_system\stocks_OHLC_3months.csv',
    index=False
)
print("✅ 保存完了: stocks_OHLC_3months.csv")