import jquantsapi
import pandas as pd
API_KEY="4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
client=jquantsapi.ClientV2(api_key=API_KEY)
print("取得中...")
df=client.get_list()
print(len(df))
print(df.columns.tolist())
df.to_csv("stock_names.csv",index=False,encoding="utf-8-sig")
print("完了")