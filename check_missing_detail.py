import pandas as pd

CSV_PATH = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"
df = pd.read_csv(CSV_PATH, dtype={"Code": str})
df["Date"] = pd.to_datetime(df["Date"])

# 欠損行を抽出
missing = df[df["Volume"].isna() | (df["Volume"] == 0)]
valid   = df[df["Volume"].notna() & (df["Volume"] != 0)]

print(f"=== 欠損の内訳 ===")
print(f"欠損行数 : {len(missing):,}")
print(f"有効行数 : {len(valid):,}")

# 日付別欠損件数
print(f"\n--- 日付別 欠損件数（上位10日）---")
print(missing.groupby("Date").size().sort_values(ascending=False).head(10))

# 欠損が多い銘柄
print(f"\n--- 銘柄別 欠損件数（上位20銘柄）---")
miss_by_code = missing.groupby(["Code","Name"]).size().sort_values(ascending=False).head(20)
print(miss_by_code)

# 有効データの日付範囲
print(f"\n--- 有効データの日付範囲 ---")
print(f"最古: {valid['Date'].min().date()}")
print(f"最新: {valid['Date'].max().date()}")
print(f"有効データの日付一覧（最新10日）:")
print(valid["Date"].drop_duplicates().sort_values(ascending=False).head(10).dt.date.tolist())

# 欠損データの日付一覧
print(f"\n--- 欠損データの日付一覧（最新10日）---")
print(missing["Date"].drop_duplicates().sort_values(ascending=False).head(10).dt.date.tolist())