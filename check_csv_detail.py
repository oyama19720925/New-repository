import pandas as pd

path = r"C:\stock_system\stocks_OHLC_20260515_20260818_merged.csv"

df = pd.read_csv(path, encoding='utf-8')
df.columns = df.columns.str.strip()

print(f"📊 総行数: {len(df)}")
print(f"📋 列数: {len(df.columns)}")
print()

# 各列のNaN率を確認
print("📈 各列のデータ充填率:")
for col in df.columns:
    non_nan = df[col].notna().sum()
    rate = non_nan / len(df) * 100
    status = "✅" if rate > 50 else "⚠️" if rate > 0 else "❌"
    print(f"  {status} {col:15s}: {non_nan:6d}件 ({rate:.1f}%)")

print()
# Nameがある行を表示
name_ok = df[df['Name'].notna()]
print(f"📌 Name列にデータがある行数: {len(name_ok)}")
if len(name_ok) > 0:
    print(name_ok.head(3).to_string())

print()
# Codeの種類確認
print(f"📌 Codeのユニーク数: {df['Code'].nunique()}")
print(f"📌 Codeサンプル: {df['Code'].unique()[:10].tolist()}")