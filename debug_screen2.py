import sys, os, inspect, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, r"C:\stock_system")

import app

# screen_stocks ソース表示
print("="*60)
print("【screen_stocks ソースコード】")
print("="*60)
try:
    print(inspect.getsource(app.screen_stocks))
except Exception as e:
    print(f"エラー: {e}")

# main内のスクリーニング関連行
print("\n" + "="*60)
print("【main内 screen/button 関連行】")
print("="*60)
try:
    lines = inspect.getsource(app.main).split('\n')
    for i, line in enumerate(lines):
        if any(kw in line for kw in ['screen','Screen','スクリーン','button','Button','tab']):
            print(f"  {i+1:4d}: {line}")
except Exception as e:
    print(f"エラー: {e}")

# screen_stocks 直接テスト
print("\n" + "="*60)
print("【screen_stocks 直接実行テスト】")
print("="*60)
try:
    import pandas as pd
    csv_files = app.get_csv_files()
    df = app.load_data(csv_files[0])
    print(f"データ: {len(df)}行")
    sig = inspect.signature(app.screen_stocks)
    print(f"引数: {sig}")
    result = app.screen_stocks(df)
    if result is None:
        print("❌ 戻り値 None")
    elif isinstance(result, pd.DataFrame):
        print(f"✅ 結果: {len(result)}行")
        if len(result) > 0:
            print(result.head(3).to_string())
    else:
        print(f"型: {type(result)}, 値: {result}")
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()