# V2では手動でAPIキーを管理します
# J-Quantsサイト(https://jpx-jquants.com/)から
# APIキーをコピーしてapi_token.txtに保存してください

import jquantsapi

# api_token.txtからAPIキーを読み込んでテスト
with open("api_token.txt", "r") as f:
    api_key = f.read().strip()

print(f"APIキー確認: {api_key[:30]}...")

# 接続テスト
client = jquantsapi.ClientV2(api_key=api_key)

try:
    # 市場カレンダーで接続確認（軽いAPI）
    df = client.get_mkt_calendar()
    print("✅ API接続成功！")
    print(df.head())
except Exception as e:
    print(f"❌ 接続失敗: {e}")