import pandas as pd

print("📂 ファイル読み込み中...")

df_price = pd.read_csv('stocks_OHLC_20260515_20260813.csv', encoding='utf-8-sig')
print(f"  価格データ: {len(df_price):,}行")

df_master = pd.read_csv('stock_master.csv', encoding='utf-8-sig')
print(f"  銘柄マスタ: {len(df_master):,}行")

df_names = df_master[['Code', 'CoName', 'S33Nm', 'MktNm']].drop_duplicates(subset='Code')
print(f"  ユニーク銘柄数: {len(df_names):,}銘柄")

df_price['Code'] = df_price['Code'].astype(str)
df_names['Code'] = df_names['Code'].astype(str)

print("\n🔗 マージ中...")
df_merged = df_price.merge(df_names, on='Code', how='left')

matched = df_merged['CoName'].notna().sum()
total = len(df_merged)
print(f"  マージ結果: {total:,}行")
print(f"  銘柄名マッチ: {matched:,}行 ({matched/total*100:.1f}%)")

df_merged = df_merged[['Date', 'Code', 'CoName', 'S33Nm', 'MktNm', 'O', 'H', 'L', 'C']]

print("\n📋 サンプル（先頭5行）:")
print(df_merged.head())

df_merged.to_csv('stocks_OHLC_with_names.csv', index=False, encoding='utf-8-sig')
print("\n✅ 保存完了: stocks_OHLC_with_names.csv")