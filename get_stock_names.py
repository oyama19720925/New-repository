import jquantsapi
import pandas as pd

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"

client = jquantsapi.ClientV2(api_key=API_KEY)

print("銘柄一覧を取得中...")

# 銘柄一覧取得
listed = client.get_list()

print(f"取得完了: {len(listed)} 銘柄")
print(listed.head())
print(f"\nカラム一覧: {listed.columns.tolist()}")

# CSVに保存
listed.to_csv("C:\\stock_system\\stock_names.csv", index=False, encoding="utf-8-sig")
print("\nstock_names.csv に保存しました！")