import jquantsapi
import pandas as pd

# APIキーを読み込み
with open("api_token.txt", "r") as f:
    api_key = f.read().strip()

print(f"APIキー: {api_key[:20]}...")

# ClientV2で接続
client = jquantsapi.ClientV2(api_key=api_key)

print("銘柄マスタを取得中...")

try:
    # V2の正しいメソッド名
    df_info = client.get_list()
    print(f"✅ 取得成功！ 銘柄数: {len(df_info)}")
    print(df_info.head())
    print(f"\nカラム一覧: {df_info.columns.tolist()}")
    
    # CSVに保存
    df_info.to_csv("stock_master.csv", index=False, encoding="utf-8-sig")
    print("✅ stock_master.csv に保存しました！")
    
except Exception as e:
    print(f"❌ エラー: {e}")