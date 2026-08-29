import pandas as pd
import os

CSV_PATH = r"C:\stock_system\stocks_OHLC_20260515_20260813_20260818_fixed.csv"

if not os.path.exists(CSV_PATH):
    print(f"❌ ファイルが見つかりません: {CSV_PATH}")
    print("\n📁 C:\\stock_system にある .csv ファイル一覧:")
    for f in os.listdir(r"C:\stock_system"):
        if f.endswith(".csv"):
            print(f"  {f}")
else:
    df = pd.read_csv(CSV_PATH, dtype={"Code": str})
    df["Date"] = pd.to_datetime(df["Date"])
    
    print("=== CSV ファイル状況 ===")
    print(f"総行数       : {len(df):,}")
    print(f"銘柄数       : {df['Code'].nunique():,}")
    print(f"最古の日付   : {df['Date'].min().date()}")
    print(f"最新の日付   : {df['Date'].max().date()}")
    print(f"列一覧       : {list(df.columns)}")
    print(f"\n最新5営業日  :")
    print(df["Date"].drop_duplicates().sort_values(ascending=False).head(10).dt.date.tolist())
    
    # ボリューム欠損確認
    if "Volume" in df.columns:
        missing_vol = df[df["Volume"].isna() | (df["Volume"] == 0)]
        print(f"\nVolume欠損行 : {len(missing_vol):,} / {len(df):,}")
    
    # 最新日のデータ確認
    latest_date = df["Date"].max()
    latest = df[df["Date"] == latest_date]
    print(f"\n最新日({latest_date.date()})のデータ件数: {len(latest):,}銘柄")