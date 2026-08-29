import pandas as pd

files = [
    'stocks_OHLC_3months.csv',
    'stocks_OHLC_20260515_20260813.csv'
]

for f in files:
    print(f'--- {f} ---')
    for enc in ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932']:
        try:
            df = pd.read_csv(f, nrows=3, encoding=enc)
            print(f'  ✅ {enc} で読めた')
            print(f'     3列目サンプル: {df.iloc[0,2]}')
            break
        except Exception as e:
            print(f'  ❌ {enc} : {e}')