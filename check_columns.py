import glob
import os
import pandas as pd

search_path = r"C:\stock_system\stocks_OHLC_*.csv"
csv_files = glob.glob(search_path)
path = max(csv_files, key=os.path.getmtime)
print(f"📂 ファイル: {path}")

for enc in ['utf-8', 'utf-8-sig', 'cp932', 'shift-jis']:
    try:
        df = pd.read_csv(path, nrows=3, encoding=enc)
        print(f"✅ エンコード: {enc}")
        print(f"📋 列名一覧: {df.columns.tolist()}")
        print(f"📄 先頭3行:")
        print(df.head(3).to_string())
        break
    except Exception as e:
        print(f"❌ {enc}: {e}")