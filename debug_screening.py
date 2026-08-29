# debug_screening.py
import pandas as pd
import numpy as np
import glob
import os

CSV_DIR = r"C:\stock_system"

# --- データ読み込み ---
pattern = os.path.join(CSV_DIR, "stocks_OHLC_*.csv")
files = glob.glob(pattern)
files.sort(key=os.path.getmtime, reverse=True)
filepath = files[0]
print(f"読み込み: {os.path.basename(filepath)}")

df = pd.read_csv(filepath, encoding="utf-8-sig", low_memory=False)
df.columns = df.columns.str.strip()
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

print(f"行数: {len(df)}, 銘柄数: {df['Code'].nunique()}")

# --- スクリーニング条件を手動テスト ---
latest_date = df["Date"].max()
print(f"\n最新日: {latest_date}")

# 最新日データ
latest_df = df[df["Date"] == latest_date].copy()
print(f"最新日レコード数: {len(latest_df)}")

# AdjC の null 除外
before = len(latest_df)
latest_df = latest_df.dropna(subset=["AdjC"])
print(f"AdjC null除外後: {len(latest_df)} (除外: {before - len(latest_df)})")

# AdjVo の null 除外
before = len(latest_df)
latest_df = latest_df.dropna(subset=["AdjVo"])
print(f"AdjVo null除外後: {len(latest_df)} (除外: {before - len(latest_df)})")

# 価格フィルタ (例: 100円以上)
before = len(latest_df)
latest_df = latest_df[latest_df["AdjC"] >= 100]
print(f"価格>=100フィルタ後: {len(latest_df)} (除外: {before - len(latest_df)})")

# 出来高フィルタ (例: 10万以上)
before = len(latest_df)
latest_df = latest_df[latest_df["AdjVo"] >= 100000]
print(f"出来高>=100000フィルタ後: {len(latest_df)} (除外: {before - len(latest_df)})")

print(f"\n✅ スクリーニング対象銘柄数: {len(latest_df)}")

# --- 各銘柄で移動平均計算テスト ---
print("\n--- 移動平均計算テスト (最初の3銘柄) ---")
codes = latest_df["Code"].head(3).tolist()
for code in codes:
    stock_df = df[df["Code"] == code].sort_values("Date").copy()
    stock_df = stock_df.dropna(subset=["AdjC"])
    
    if len(stock_df) < 25:
        print(f"  {code}: データ不足 ({len(stock_df)}日)")
        continue
    
    stock_df["MA5"]  = stock_df["AdjC"].rolling(5).mean()
    stock_df["MA25"] = stock_df["AdjC"].rolling(25).mean()
    
    last = stock_df.iloc[-1]
    print(f"  {code}: AdjC={last['AdjC']:.1f}, MA5={last['MA5']:.1f}, MA25={last['MA25']:.1f}")
    
    # ゴールデンクロス条件
    if len(stock_df) >= 2:
        prev = stock_df.iloc[-2]
        gc = (last["MA5"] > last["MA25"]) and (prev["MA5"] <= prev["MA25"])
        print(f"    → GC条件: {gc}")

# --- app.py のスクリーニング関数を直接テスト ---
print("\n--- app.py インポートテスト ---")
try:
    import sys
    sys.path.insert(0, CSV_DIR)
    import app
    print("✅ app.py インポート成功")
    
    # スクリーニング関数があるか確認
    if hasattr(app, 'run_screening'):
        print("✅ run_screening 関数あり")
    else:
        print("❌ run_screening 関数なし")
        
    if hasattr(app, 'screening'):
        print("✅ screening 関数あり")
    else:
        print("❌ screening 関数なし")
        
    # 関数一覧
    funcs = [f for f in dir(app) if not f.startswith('_')]
    print(f"定義済み関数/変数: {funcs}")
    
except Exception as e:
    print(f"❌ app.py インポートエラー: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 診断完了")