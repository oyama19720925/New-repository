import jquantsapi
import pandas as pd

# APIキーを設定
client = jquantsapi.ClientV2(api_key="4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")

print("銘柄マスター取得中...")

try:
    df = client.get_list()
    print(f"✅ get_list() 成功: {len(df)} 銘柄")
    print("列名:", df.columns.tolist())
    print(df.head(3))
    df.to_csv("stock_names.csv", index=False, encoding="utf-8-sig")
    print("stock_names.csv に保存しました")

except Exception as e:
    print(f"❌ エラー発生: {type(e).__name__}: {e}")
    
    # 利用可能なメソッドを全て表示
    print("\n📋 利用可能なメソッド一覧:")
    methods = [m for m in dir(client) if not m.startswith('_')]
    for m in methods:
        print(f"  - {m}")