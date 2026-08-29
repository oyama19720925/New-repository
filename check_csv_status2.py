import pandas as pd
import os

# 候補ファイルを全て確認
files = [
    r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv",
    r"C:\stock_system\stocks_OHLC_20260515_20260818_merged.csv",
    r"C:\stock_system\stocks_OHLC_3months.csv",
]

for CSV_PATH in files:
    if not os.path.exists(CSV_PATH):
        continue
    print(f"\n{'='*60}")
    print(f"📄 {os.path.basename(CSV_PATH)}")
    print(f"{'='*60}")
    try:
        df = pd.read_csv(CSV_PATH, dtype={"Code": str})
        df["Date"] = pd.to_datetime(df["Date"])
        print(f"  総行数     : {len(df):,}")
        print(f"  銘柄数     : {df['Code'].nunique():,}")
        print(f"  最古の日付 : {df['Date'].min().date()}")
        print(f"  最新の日付 : {df['Date'].max().date()}")
        print(f"  列一覧     : {list(df.columns)}")
        if "Volume" in df.columns:
            missing_vol = df[df["Volume"].isna() | (df["Volume"] == 0)]
            print(f"  Volume欠損 : {len(missing_vol):,} 行")
        if "AdjC" in df.columns:
            missing_adj = df[df["AdjC"].isna()]
            print(f"  AdjC欠損   : {len(missing_adj):,} 行")
    except Exception as e:
        print(f"  ❌ エラー: {e}")