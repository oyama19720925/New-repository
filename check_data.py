import pandas as pd
import glob
import os

csv_files = glob.glob(r'C:\stock_system\*.csv')
print("=== 見つかったCSVファイル ===")
for f in csv_files:
    size = os.path.getsize(f) / 1024 / 1024
    print(f"  {os.path.basename(f)} ({size:.1f} MB)")

largest = max(csv_files, key=os.path.getsize)
print(f"\n=== 自動選択: {os.path.basename(largest)} ===")

df = pd.read_csv(largest)
print(f"列名: {list(df.columns)}")
print(f"開始日: {df['Date'].min()}")
print(f"終了日: {df['Date'].max()}")
print(f"行数: {len(df):,}")
print(f"銘柄数: {df['Code'].nunique():,}")