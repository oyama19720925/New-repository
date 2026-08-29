import pandas as pd
import os

csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]

for fname in csv_files:
    try:
        df = pd.read_csv(fname, encoding='utf-8-sig')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            print(f"\n📄 {fname}")
            print(f"   行数: {len(df):,}")
            print(f"   最古: {df['Date'].min().strftime('%Y-%m-%d')}")
            print(f"   最新: {df['Date'].max().strftime('%Y-%m-%d')}")
            print(f"   銘柄数: {df['Code'].nunique() if 'Code' in df.columns else 'N/A'}")
        else:
            print(f"\n📄 {fname} → Dateカラムなし")
    except Exception as e:
        print(f"\n📄 {fname} → エラー: {e}")