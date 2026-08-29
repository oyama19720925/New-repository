# add_names.py
import jquantsapi
import pandas as pd

# =============================
# APIキーを設定してください
# =============================
API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"  # ← 実際のAPIキーに変更

client = jquantsapi.ClientV2(api_key=API_KEY)

# 銘柄一覧を取得
print("📡 銘柄一覧を取得中...")
try:
    listed_df = client.get_list()
    print(f"✅ 取得成功: {len(listed_df)}銘柄")
except Exception as e:
    print(f"❌ 取得失敗: {e}")
    exit()

# Codeを文字列に統一
listed_df['Code'] = listed_df['Code'].astype(str).str.strip()

print(f"🔍 銘柄一覧のCode例: {listed_df['Code'].head(5).tolist()}")
print(f"🔍 CoName例: {listed_df['CoName'].head(5).tolist()}")

# 既存CSVを読み込み
print("\n📂 OHLCデータを読み込み中...")

# CSVファイル名を自動検索
import glob
csv_files = glob.glob('stocks_OHLC_*.csv')
csv_files = [f for f in csv_files if 'with_names' not in f]
print(f"📋 見つかったCSV: {csv_files}")

if not csv_files:
    print("❌ OHLCのCSVファイルが見つかりません")
    exit()

# 最新のCSVを使用
csv_file = sorted(csv_files)[-1]
print(f"✅ 使用するCSV: {csv_file}")

df = pd.read_csv(csv_file, dtype={'Code': str})
df['Code'] = df['Code'].astype(str).str.strip()
print(f"✅ {len(df)}行 読み込み完了")
print(f"🔍 OHLCのCode例: {df['Code'].head(5).tolist()}")
print(f"🔍 OHLC列名: {df.columns.tolist()}")

# Codeの桁数を合わせる（4桁 vs 5桁の問題対策）
ohlc_code_len = df['Code'].str.len().mode()[0]
list_code_len = listed_df['Code'].str.len().mode()[0]
print(f"\n🔍 OHLCのCode桁数: {ohlc_code_len}")
print(f"🔍 銘柄一覧のCode桁数: {list_code_len}")

if ohlc_code_len != list_code_len:
    if ohlc_code_len < list_code_len:
        # OHLCが短い → 0を末尾に追加（例: 1301 → 13010）
        df['Code'] = df['Code'].str.zfill(list_code_len)
        print(f"⚠️ OHLCのCodeを{list_code_len}桁に変換")
    else:
        # 銘柄一覧が短い → 0を末尾に追加
        listed_df['Code'] = listed_df['Code'].str.zfill(ohlc_code_len)
        print(f"⚠️ 銘柄一覧のCodeを{ohlc_code_len}桁に変換")

# マージ
print("\n🔗 銘柄名をマージ中...")
df = df.merge(
    listed_df[['Code', 'CoName']],
    on='Code',
    how='left'
)

# マージ結果確認
matched = df['CoName'].notna().sum()
total = len(df)
print(f"\n📊 マージ結果:")
print(f"  総行数    : {total:,}")
print(f"  マッチ数  : {matched:,}")
print(f"  マッチ率  : {matched/total*100:.1f}%")
print(f"  列名      : {df.columns.tolist()}")
print(df[['Date', 'Code', 'CoName']].head(10))

# 保存
output_file = 'stocks_OHLC_with_names.csv'
df.to_csv(output_file, index=False)
print(f"\n✅ 保存完了: {output_file}")
print(f"📁 ファイルサイズ確認:")

import os
size = os.path.getsize(output_file) / 1024 / 1024
print(f"  {output_file}: {size:.1f} MB")