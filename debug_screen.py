# debug_screen.py
import pandas as pd
import numpy as np
import glob, os

DATA_DIR = r"C:\stock_system"

# 最新CSV取得
files = glob.glob(os.path.join(DATA_DIR, "stocks_OHLC_*.csv"))
files.sort(key=os.path.getmtime, reverse=True)
csv_path = files[0]
print(f"CSV: {csv_path}")

df = pd.read_csv(csv_path, dtype={"Code": str})
df["Date"] = pd.to_datetime(df["Date"])

print(f"\n=== DataFrame列名 ===")
print(df.columns.tolist())

print(f"\n=== 先頭5行 ===")
print(df.head())

print(f"\n=== 最新日付 ===")
latest_date = df["Date"].max()
print(f"latest_date: {latest_date}")

latest = df[df["Date"] == latest_date].copy()
print(f"latest行数: {len(latest)}")
print(f"latest列名: {latest.columns.tolist()}")

# run_screeningの簡易実行
print(f"\n=== スクリーニング試行 ===")
# AdjVoフィルタ
vol_min = 100_000
mktcap_min = 1_000 * 1e6

if "AdjVo" in latest.columns:
    latest = latest[latest["AdjVo"] >= vol_min]
    print(f"AdjVoフィルタ後: {len(latest)}行")
else:
    print(f"⚠️ AdjVo列が存在しない！")

if "MktCap" in latest.columns:
    latest = latest[latest["MktCap"] >= mktcap_min]
    print(f"MktCapフィルタ後: {len(latest)}行")
else:
    print(f"⚠️ MktCap列が存在しない！")

print(f"\n=== resultsサンプル ===")
results = []
codes = latest["Code"].unique() if "Code" in latest.columns else []
print(f"対象コード数: {len(codes)}")

# 最初の3銘柄だけ試す
for code in list(codes)[:3]:
    stock_df = df[df["Code"] == code].sort_values("Date").tail(80)
    row = latest[latest["Code"] == code].iloc[0]
    price = row["AdjC"]
    adj = stock_df["AdjC"]
    ma5 = adj.rolling(5).mean().iloc[-1]
    ma25 = adj.rolling(25).mean().iloc[-1]
    results.append({
        "Code": code,
        "Name": row.get("Name", ""),
        "Close": round(price, 1),
        "MA5": round(ma5, 1),
        "MA25": round(ma25, 1),
    })
    print(f"  {code}: OK")

result_df = pd.DataFrame(results)
print(f"\n=== result_df列名 ===")
print(result_df.columns.tolist())
print(result_df)