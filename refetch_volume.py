# refetch_volume.py（完全修正版）
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY")
HEADERS = {"x-api-key": API_KEY}
BASE_URL = "https://api.jquants.com"

# ✅ 正しいファイル名に修正
CSV_PATH = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"
OUT_PATH = r"C:\stock_system\api_volume_data.csv"

print("📂 CSV読み込み中...")
df = pd.read_csv(CSV_PATH, encoding='utf-8', low_memory=False)
df.columns = df.columns.str.strip()
print(f"   行数: {len(df):,}行")
print(f"   列名: {list(df.columns)}")

# Volume欠損の日付範囲を特定
df['Date'] = pd.to_datetime(df['Date'])

if 'Volume' not in df.columns:
    print("❌ Volume列が見つかりません！")
    exit()

missing_mask = df['Volume'].isna()
print(f"\n📊 Volume欠損: {missing_mask.sum():,}行 / 全{len(df):,}行")

if missing_mask.sum() == 0:
    print("✅ Volume欠損なし！処理終了")
    exit()

# ✅ sorted()を使用（DatetimeArray対応）
missing_dates = sorted(df[missing_mask]['Date'].unique())
date_from = pd.Timestamp(missing_dates[0]).strftime('%Y%m%d')
date_to   = pd.Timestamp(missing_dates[-1]).strftime('%Y%m%d')

print(f"📅 Volume欠損期間: {date_from} ～ {date_to}")
print(f"   対象日数: {len(missing_dates)}日")

# APIから一括取得
print(f"\n🌐 APIからデータ取得中...")
url = f"{BASE_URL}/equities/bars/daily"
params = {
    "date_from": date_from,
    "date_to":   date_to
}

all_data = []
page = 1

while True:
    print(f"  📄 Page {page} 取得中...", end=" ")
    resp = requests.get(url, headers=HEADERS, params=params)
    print(f"status={resp.status_code}")

    if resp.status_code != 200:
        print(f"  ❌ エラー: {resp.text[:300]}")
        break

    data = resp.json()

    if page == 1:
        print(f"  🔑 レスポンスキー: {list(data.keys())}")

    # データ抽出（キー名を自動判定）
    records = (
        data.get('bars') or
        data.get('daily_quotes') or
        data.get('data') or
        []
    )

    if not records:
        print(f"  ✅ 全ページ取得完了")
        break

    all_data.extend(records)
    print(f"     取得: {len(records):,}件 / 累計: {len(all_data):,}件")