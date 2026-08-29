import pandas as pd

path = r"C:\stock_system\stocks_OHLC_20260515_20260818_merged.csv"
df = pd.read_csv(path, encoding='utf-8', low_memory=False)
df.columns = df.columns.str.strip()

# Nameがある行とない行に分離
df_with_name = df[df['Name'].notna()]
df_no_name = df[df['Name'].isna()]

print(f"✅ Name有り: {len(df_with_name)}行")
print(f"❌ Name無し: {len(df_no_name)}行")
print()

# Name無しのCodeサンプル
print("❌ Name無しのCodeサンプル（先頭20件）:")
print(df_no_name['Code'].unique()[:20].tolist())
print()

# Name有りのCodeサンプル
print("✅ Name有りのCodeサンプル（先頭20件）:")
print(df_with_name['Code'].unique()[:20].tolist())
print()

# Dateの分布確認
print("📅 Name無しの日付範囲:")
print(f"  最古: {df_no_name['Date'].min()}")
print(f"  最新: {df_no_name['Date'].max()}")
print()
print("📅 Name有りの日付範囲:")
print(f"  最古: {df_with_name['Date'].min()}")
print(f"  最新: {df_with_name['Date'].max()}")
print()

# Codeの重複確認
codes_with = set(df_with_name['Code'].unique())
codes_without = set(df_no_name['Code'].unique())
overlap = codes_with & codes_without
print(f"🔄 両方に存在するCode数: {len(overlap)}")
print(f"📌 Name有りのみのCode数: {len(codes_with - codes_without)}")
print(f"📌 Name無しのみのCode数: {len(codes_without - codes_with)}")