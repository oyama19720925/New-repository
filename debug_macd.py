import pandas as pd
import numpy as np
import glob

# CSVファイルを探す
files = glob.glob("*.csv")
print("CSVファイル一覧:")
for f in files:
    print(" ", f)

if not files:
    print("CSVファイルが見つかりません！")
    exit()

# 最初のCSVを読み込む
target = files[0]
print(f"\n読み込み: {target}")
df = pd.read_csv(target, low_memory=False)

print("\n=== カラム名 ===")
print(df.columns.tolist())

print("\n=== 行数・銘柄数 ===")
print(f"行数: {len(df)}")

# 銘柄数を確認
for col in ['Code', 'code', 'コード', 'Symbol', 'Ticker']:
    if col in df.columns:
        print(f"銘柄数: {df[col].nunique()} (カラム: {col})")
        break

print("\n=== 先頭5行 ===")
print(df.head())

print("\n=== データ型 ===")
print(df.dtypes)

# Closeカラムを確認
close_candidates = ['Close', 'close', '終値', 'AdjustmentClose']
for col in close_candidates:
    if col in df.columns:
        print(f"\n終値カラム '{col}' の統計:")
        print(df[col].describe())
        break