import pandas as pd
from pathlib import Path

RENAME_MAP = {
    'Date':   'Date', 'date':   'Date', 'DATE':   'Date',
    'Code':   'Code', 'code':   'Code', 'Cd':     'Code',
    'Name':   'Name', 'CoName': 'Name', 'name':   'Name',
    'Sector': 'Sector', 'S33Nm': 'Sector', 'sector': 'Sector',
    'Market': 'Market', 'MktNm': 'Market', 'market': 'Market',
    'Open':   'Open', 'O':      'Open',
    'High':   'High', 'H':      'High',
    'Low':    'Low',  'L':      'Low',
    'Close':  'Close','C':      'Close',
    'Volume': 'Volume','Vo':    'Volume', 'Vol':   'Volume',
}

def load_and_normalize(filepath):
    df = None
    used_enc = None
    for enc in ['utf-8', 'utf-8-sig', 'cp932', 'shift-jis']:
        try:
            df = pd.read_csv(filepath, encoding=enc, low_memory=False)
            used_enc = enc
            break
        except Exception:
            continue
    if df is None:
        print(f'  ERROR: {filepath.name}')
        return None
    print(f'  OK: {filepath.name}')
    print(f'     文字コード : {used_enc}')
    print(f'     元の列名   : {df.columns.tolist()}')
    print(f'     行数       : {len(df):,}行')
    df.rename(columns=RENAME_MAP, inplace=True)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if 'Code' in df.columns:
        df['Code'] = df['Code'].astype(str).str.strip()
    print(f'     統一後列名 : {df.columns.tolist()}')
    return df

print('=' * 50)
print('CSVファイルを検索中...')
print('=' * 50)

csv_files = sorted(Path('.').glob('stocks_OHLC*.csv'))

if not csv_files:
    print('ERROR: stocks_OHLC*.csv が見つかりません')
    exit()

print(f'対象ファイル: {len(csv_files)}個\n')

dfs = []
for f in csv_files:
    print(f'--- 処理中: {f.name} ---')
    df = load_and_normalize(f)
    if df is not None:
        dfs.append(df)
    print()

if not dfs:
    print('ERROR: 読み込めるファイルがありませんでした')
    exit()

print('=' * 50)
print('マージ中...')

df_merged = pd.concat(dfs, ignore_index=True)
before = len(df_merged)

df_merged.drop_duplicates(subset=['Date', 'Code'], inplace=True)
after = len(df_merged)

df_merged.sort_values(['Code', 'Date'], inplace=True)
df_merged.reset_index(drop=True, inplace=True)

print(f'  結合前の行数 : {before:,}行')
print(f'  重複除去後   : {after:,}行')
print(f'  銘柄数       : {df_merged["Code"].nunique():,}銘柄')

date_min = df_merged['Date'].min().strftime('%Y-%m-%d')
date_max = df_merged['Date'].max().strftime('%Y-%m-%d')
print(f'  期間         : {date_min} から {date_max}')

output_file = f'stocks_OHLC_{date_min.replace("-","")}_{date_max.replace("-","")}_merged.csv'
df_merged.to_csv(output_file, index=False, encoding='utf-8-sig')

print()
print('=' * 50)
print(f'保存完了: {output_file}')
print(f'列名: {df_merged.columns.tolist()}')
print('=' * 50)