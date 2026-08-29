import pandas as pd
import requests
from datetime import datetime, timedelta

print("CSVファイル読み込み中...")
df = pd.read_csv(r'C:\stock_system\stocks_OHLC_3months_20260819.csv', dtype={'Code': str})

print(f"  読み込み前: {len(df):,} レコード")
print(f"  期間: {df['Date'].min()} 〜 {df['Date'].max()}")

cutoff = (datetime.today() - timedelta(days=92)).strftime('%Y-%m-%d')
df = df[df['Date'] >= cutoff].copy()
print(f"  フィルタ後: {len(df):,} レコード ({cutoff} 以降)")

df = df.rename(columns={
    'O': 'Open',
    'H': 'High',
    'L': 'Low',
    'C': 'Close',
    'Vo': 'Volume',
})

API_KEY = '4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU'
headers = {'x-api-key': API_KEY}

print("銘柄マスタ取得中...")
resp = requests.get('https://api.jquants.com/v2/equities/master', headers=headers)
raw = resp.json()

key = None
for k in ['equities', 'items', 'data', 'Equities']:
    if k in raw:
        key = k
        break

if key is None:
    print(f"ERROR: 想定外のキー: {list(raw.keys())}")
    exit()

master = pd.DataFrame(raw[key])
print(f"  マスタ列名: {master.columns.tolist()}")
print(f"  マスタ行数: {len(master):,}")

master_sub = master[['Code', 'CoName', 'S17Nm', 'MktNm']].copy()
master_sub = master_sub.rename(columns={
    'CoName': 'Name',
    'S17Nm': 'Sector',
    'MktNm': 'Market',
})

master_sub['Code'] = master_sub['Code'].astype(str)
df['Code'] = df['Code'].astype(str)

before = len(df)
df = df.merge(master_sub, on='Code', how='left')
print(f"  マスタ結合完了: {before:,} -> {len(df):,} レコード")

desired_cols = [
    'Date', 'Code', 'Open', 'High', 'Low', 'Close',
    'Name', 'Sector', 'Market',
    'UL', 'LL', 'Volume', 'Va',
    'AdjFactor', 'AdjO', 'AdjH', 'AdjL', 'AdjC', 'A