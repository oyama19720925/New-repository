import jquantsapi
import pandas as pd
import time
from datetime import datetime, timedelta

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"

cli = jquantsapi.ClientV2(api_key=API_KEY)

# ✅ 7月・8月だけ再取得（5月・6月は既に取得済み）
periods = [
    ("20260701", "20260731"),
    ("20260801", "20260813"),
]

all_df = []

print("7月・8月データ 再取得開始")
print("=" * 50)

for date_from, date_to in periods:
    print(f"取得中: {date_from} 〜 {date_to} ...", end=" ")

    # リトライ処理（最大5回）
    for retry in range(5):
        try:
            df = cli.get_eq_bars_daily_range(
                start_dt=date_from,
                end_dt=date_to
            )

            # ✅ 必要な列だけ抽出
            df = df[['Date', 'Code', 'O', 'H', 'L', 'C']]

            all_df.append(df)
            print(f"✅ {len(df):,}行 ({df['Code'].nunique():,}銘柄)")
            break  # 成功したらリトライ終了

        except Exception as e:
            print(f"\n  ⚠️ エラー(試行{retry+1}/5): {e}")
            wait_time = 60 * (retry + 1)  # 60秒、120秒、180秒...と増加
            print(f"  ⏳ {wait_time}秒待機中...", end=" ")
            time.sleep(wait_time)
            print("再試行")

    # 月間リクエスト後に十分待機
    print("  ⏳ 次の月まで60秒待機...")
    time.sleep(60)

# 既存CSVと結合
print("\n既存データと結合中...")
try:
    existing_df = pd.read_csv(
        "stocks_OHLC_20260515_20260813.csv",
        encoding="utf-8-sig"
    )
    print(f"既存データ: {len(existing_df):,}行")
    all_df.insert(0, existing_df)
except:
    print("既存ファイルが見つからないため新規作成")

if all_df:
    final_df = pd.concat(all_df, ignore_index=True)

    # 日付型に変換してソート
    final_df['Date'] = pd.to_datetime(final_df['Date'])
    final_df = final_df.sort_values(['Code', 'Date']).reset_index(drop=True)

    # 重複削除
    final_df = final_df.drop_duplicates(subset=['Date', 'Code'])

    print("=" * 50)
    print(f"\n✅ 全取得完了！")
    print(f"総データ件数: {len(final_df):,}行")
    print(f"銘柄数: {final_df['Code'].nunique():,}銘柄")
    print(f"期間: {final_df['Date'].min()} 〜 {final_df['Date'].max()}")
    print(f"\n先頭5行:")
    print(final_df.head())

    # 最終CSV保存
    final_df.to_csv(
        "stocks_OHLC_3months.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print(f"\n💾 最終CSV保存完了: stocks_OHLC_3months.csv")

