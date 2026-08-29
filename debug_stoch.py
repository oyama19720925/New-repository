import pandas as pd
import numpy as np
import glob

csv_files = glob.glob("*.csv")
csv_files = [f for f in csv_files if "stock" in f.lower() or "ohlc" in f.lower()]

if not csv_files:
    print("CSVファイルが見つかりません")
    exit()

filepath = csv_files[0]
print(f"使用ファイル: {filepath}")

df_all = pd.read_csv(filepath, dtype={"Code": str}, low_memory=False)
df_all["Date"] = pd.to_datetime(df_all["Date"])
df_all = df_all.sort_values(["Code", "Date"]).reset_index(drop=True)

print(f"列名一覧: {df_all.columns.tolist()}")
print(f"行数: {len(df_all):,}")
print(f"銘柄数: {df_all['Code'].nunique():,}")

col_c = "C" if "C" in df_all.columns else "Close"
col_h = "H" if "H" in df_all.columns else "High"
col_l = "L" if "L" in df_all.columns else "Low"

hit = 0
nan_c = 0
short_c = 0

for code in df_all["Code"].unique():
    d = df_all[df_all["Code"] == code].copy()
    if len(d) < 20:
        short_c += 1
        continue
    low14  = d[col_l].rolling(14).min()
    high14 = d[col_h].rolling(14).max()
    k = (d[col_c] - low14) / (high14 - low14).replace(0, np.nan) * 100
    dk = k.rolling(3).mean()
    lk = k.iloc[-1]
    ld = dk.iloc[-1]
    if pd.isna(lk) or pd.isna(ld):
        nan_c += 1
        continue
    if 20 <= lk <= 80 and 20 <= ld <= 80:
        hit += 1

print(f"ヒット数(K:20-80,D:20-80): {hit}")
print(f"NaNで除外: {nan_c}")
print(f"データ不足で除外: {short_c}")