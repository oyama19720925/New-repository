# fix_volume_from_3months.py
import pandas as pd

PATH_FIXED   = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"
PATH_3MONTHS = r"C:\stock_system\stocks_OHLC_3months.csv"
PATH_OUT     = r"C:\stock_system\stocks_OHLC_20260515_20260818_complete.csv"

print("📂 データ読み込み中...")
df_fixed = pd.read_csv(PATH_FIXED,   dtype={"Code": str}, low_memory=False)
df_3m    = pd.read_csv(PATH_3MONTHS, dtype={"Code": str}, low_memory=False)

df_fixed["Date"] = pd.to_datetime(df_fixed["Date"])
df_3m["Date"]    = pd.to_datetime(df_3m["Date"])

# 3months.csv の列名を fixed に合わせてリネーム
rename_map = {
    "O": "Open", "H": "High", "L": "Low", "C": "Close",
    "CoName": "Name", "S33Nm": "Sector", "MktNm": "Market",
    "Vo": "Volume"
}
df_3m = df_3m.rename(columns=rename_map)

print(f"  fixed   行数: {len(df_fixed):,}")
print(f"  3months 行数: {len(df_3m):,}")

# 3months.csv から Volume と Va を抽出（補完用）
cols_supplement = ["Date", "Code", "Volume", "Va",
                   "AdjFactor", "AdjO", "AdjH", "AdjL", "AdjC", "AdjVo",
                   "MktCap", "ExRT"]
# 存在する列のみ選択
cols_supplement = [c for c in cols_supplement if c in df_3m.columns]
df_3m_sub = df_3m[cols_supplement].copy()

print(f"\n🔄 Volume欠損行を補完中...")

# fixedのVolume欠損行を特定
missing_mask = df_fixed["Volume"].isna() | (df_fixed["Volume"] == 0)
print(f"  補完対象行数: {missing_mask.sum():,}")

# マージキー
df_fixed = df_fixed.merge(
    df_3m_sub,
    on=["Date", "Code"],
    how="left",
    suffixes=("", "_3m")
)

# 欠損している列を3monthsデータで埋める
fill_cols = ["Volume", "Va", "AdjFactor", "AdjO", "AdjH", "AdjL", "AdjC", "AdjVo", "MktCap", "ExRT"]
for col in fill_cols:
    col_3m = col + "_3m"
    if col_3m in df_fixed.columns:
        df_fixed[col] = df_fixed[col].fillna(df_fixed[col_3m])
        df_fixed = df_fixed.drop(columns=[col_3m])

# 結果確認
still_missing = df_fixed["Volume"].isna() | (df_fixed["Volume"] == 0)
print(f"  補完後の欠損行数: {still_missing.sum():,}")
print(f"  補完成功行数: {missing_mask.sum() - still_missing.sum():,}")

# 保存
df_fixed.to_csv(PATH_OUT, index=False)
print(f"\n✅ 保存完了: {PATH_OUT}")
print(f"   総行数: {len(df_fixed):,}")