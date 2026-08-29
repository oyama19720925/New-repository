import pandas as pd
import glob

# CSVファイルを自動検出
files = glob.glob('*.csv')
print(f'CSVファイル: {files}')

df = pd.read_csv(files[0], dtype={'Code': str})
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(['Code', 'Date'])

print(f'\n総行数: {len(df)}')
print(f'期間: {df["Date"].min()} ～ {df["Date"].max()}')
print(f'銘柄数: {df["Code"].nunique()}')

# 各銘柄のデータ日数を確認
days_per_stock = df.groupby('Code').size()
print(f'\n1銘柄あたりのデータ日数:')
print(f'  最小: {days_per_stock.min()}日')
print(f'  最大: {days_per_stock.max()}日')
print(f'  平均: {days_per_stock.mean():.1f}日')
print(f'  75日以上ある銘柄: {(days_per_stock >= 75).sum()}銘柄')
print(f'  25日以上ある銘柄: {(days_per_stock >= 25).sum()}銘柄')

# MA5/25でゴールデンクロス検索（列名は'C'）
short, long = 5, 25
hits = []
for code, group in df.groupby('Code'):
    g = group.copy().reset_index(drop=True)
    g['MA_S'] = g['C'].rolling(short).mean()
    g['MA_L'] = g['C'].rolling(long).mean()
    g = g.dropna()
    if len(g) < 2:
        continue
    today = g.iloc[-1]
    yest  = g.iloc[-2]
    if today['MA_S'] > today['MA_L'] and yest['MA_S'] <= yest['MA_L']:
        hits.append(code)

print(f'\n✅ MA{short}/MA{long} ゴールデンクロス: {len(hits)}銘柄')
if hits:
    print(f'   該当銘柄: {hits[:10]}')

# MA13/75でゴールデンクロス検索
short2, long2 = 13, 75
hits2 = []
for code, group in df.groupby('Code'):
    g = group.copy().reset_index(drop=True)
    g['MA_S'] = g['C'].rolling(short2).mean()
    g['MA_L'] = g['C'].rolling(long2).mean()
    g = g.dropna()
    if len(g) < 2:
        continue
    today = g.iloc[-1]
    yest  = g.iloc[-2]
    if today['MA_S'] > today['MA_L'] and yest['MA_S'] <= yest['MA_L']:
        hits2.append(code)

print(f'✅ MA{short2}/MA{long2} ゴールデンクロス: {len(hits2)}銘柄')
if hits2:
    print(f'   該当銘柄: {hits2[:10]}')
else:
    print('   ⚠️ 該当なし（データ期間が短い可能性あり）')