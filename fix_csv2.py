import pandas as pd
import requests
from datetime import datetime, timedelta

SRC = r'C:\stock_system\stocks_OHLC_3months_20260819.csv'
API_KEY = '4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU'

print("=== Step1: CSV読み込み ===")
df = pd.read_csv(SRC, dtype={'Code': str})
print(f"行数: {len(df):,}")
print(f"列名: {df.columns.tolist()}")
print(f"期間: {df['Date'].min()} - {df['Date'].max()}")

print("\n=== Step2: 3ヶ月フィルタ ===")
cutoff = (datetime.today() - timedelta(days=92)).strftime('%Y-%m-%d')
df = df[df['Date'] >= cutoff].copy()
print(f"フィルタ後: {len(df):,} 行 ({cutoff} 以降)")

print("\n=== Step3: 列名リネーム ===")
rename_map = {}
if 'O' in df.columns: rename_map['O'] = 'Open'
if 'H' in df.columns: rename_map['H'] = 'High'
if 'L' in df.columns: rename_map['L'] = 'Low'
if 'C' in df.columns: rename_map['C'] = 'Close'
if 'Vo' in df.columns: rename_map['Vo'] = 'Volume'
if rename_map:
    df = df.rename(columns=rename_map)
    print(f"リネーム: {rename_map}")
else:
    print("リネーム不要")

print("\n=== Step4: マスタ取得 ===")
headers = {'x-api-key': API_KEY}
resp = requests.get('https://api.jquants.com/v2/equities/master', headers=headers)
raw = resp.json()
print(f"レスポンスキー: {list(raw.keys())}")

for k in ['equities', 'Equities', 'items', 'data']:
    if k in raw:
        master = pd.DataFrame(raw[k])
        break

print(f"マスタ列名: {master.columns.tolist()}")
print(f"マスタ行数: {len(master):,}")
print(f"サンプル:\n{master.head(2).to_string()}")

print("\n=== Step5: マスタ列選択 ===")
code_col = 'Code'
name_col = None
sect_col = None
mkt_col = None

for c in master.columns:
    cl = c.lower()
    if 'coname' in cl and 'en' not in cl:
        name_col = c
    elif 's17nm' in cl:
        sect_col = c
    elif 'mktnm' in cl:
        mkt_col = c

print(f"Code={code_col}, Name={name_col}, Sector={sect_col}, Market={mkt_col}")

keep = [code_col]
rename2 = {}
if name_col:
    keep.append(name_col)
    rename2[name_col] = 'Name'
if sect_col:
    keep.append(sect_col)
    rename2[sect_col] = 'Sector'
if mkt_col:
    keep.append(mkt_col)
    rename2[mkt_col] = 'Market'

master_sub = master[keep].copy().rename(columns=rename2)
master_sub['Code'] = master_sub['Code'].astype(str)
df['Code'] = df['Code'].astype(str)

print("\n=== Step6: マスタ結合 ===")
df = df.merge(master_sub, on='Code', how='left')
print(f"結合後: {len(df):,} 行")

print("\n=== Step7: 列順序整理 ===")
front = ['Date','Code','Open','High','Low','Close','Name','Sector','Market']
back = ['UL','LL','Volume','Va','AdjFactor','AdjO','AdjH','AdjL','AdjC','AdjVo','MktCap','ExRT']
ordered = [c for c in front if c in df.columns]
ordered += [c for c in back if c in df.columns]
ordered += [c for c in df.columns if c not in ordered]
df = df[ordered]

print("\n=== Step8: 保存 ===")
today = datetime.today().strftime('%Y%m%d')
outfile = rf'C:\stock_system\stocks_OHLC_3months_{today}_fixed.csv'
df.to_csv(outfile, index=False, encoding='utf-8-sig')

print(f"ファイル: {outfile}")
print(f"レコード数: {len(df):,}")
print(f"銘柄数: {df['Code'].nunique():,}")
print(f"期間: {df['Date'].min()} - {df['Date'].max()}")
print(f"列名: {df.columns.tolist()}")

for col in ['Name','Sector','Market']:
    if col in df.columns:
        ok = df[col].notna().sum()
        print(f"  {col}: {ok:,}/{len(df):,} ({ok/len(df)*100:.1f}%)")
