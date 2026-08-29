# fetch_3months.py - 高速版（日付ごと全銘柄一括取得）
import glob
import io
import os
import sys
import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import requests

# Windows環境での絵文字出力エラー(cp932 UnicodeEncodeError)対策
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))


# ─────────────────────────────────────────
# 1. 既存CSVの最新日付を取得
# ─────────────────────────────────────────
def get_latest_csv():
    pattern = os.path.join(SAVE_DIR, "stocks_OHLC_*.csv")
    files = glob.glob(pattern)
    if not files:
        # stocks_*.csv 形式も探す
        files = glob.glob(os.path.join(SAVE_DIR, "stocks_*.csv"))
        if not files:
            return None, None
    latest = max(files, key=os.path.getmtime)
    print(f"📂 既存CSV: {os.path.basename(latest)}")
    try:
        df = pd.read_csv(latest, dtype={"Code": str})
        return latest, df
    except Exception as e:
        print(f"⚠️ 既存CSV読み込み失敗: {e}")
        return None, None


def get_last_date(df):
    if df is None or "Date" not in df.columns or df.empty:
        return None
    try:
        df["Date"] = pd.to_datetime(df["Date"])
        last = df["Date"].max()
        print(f"📅 既存データ最終日: {last.strftime('%Y-%m-%d')}")
        return last.date()
    except Exception:
        return None


# ─────────────────────────────────────────
# 2. 営業日カレンダー取得
# ─────────────────────────────────────────
def get_trading_days(start_date, end_date):
    params = {
        "holidayDivision": "1",
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
    }
    try:
        resp = requests.get(
            f"{BASE_URL}/markets/calendar",
            headers=HEADERS,
            params=params,
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if "trading_calendar" in data:
                cal = data["trading_calendar"]
            elif "data" in data:
                cal = data["data"]
            else:
                cal = data if isinstance(data, list) else []

            trading_days = []
            for item in cal:
                d_str = (
                    item.get("Date")
                    or item.get("date")
                    or item.get("TradeDate")
                )
                if d_str:
                    d = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
                    if start_date <= d <= end_date:
                        trading_days.append(d)

            trading_days.sort()
            print(f"📆 取得対象営業日: {len(trading_days)}日")
            return trading_days
    except Exception as e:
        print(f"⚠️ カレンダー取得例外: {e}")

    # 失敗時の土日除外フォールバック
    print("⚠️ 土日除外で代替営業日リストを作成します")
    days = []
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


# ─────────────────────────────────────────
# 3. 1日分の全銘柄データを取得
# ─────────────────────────────────────────
def fetch_one_day(target_date):
    params = {"date": target_date.strftime("%Y-%m-%d")}
    for attempt in range(3):
        try:
            resp = requests.get(
                f"{BASE_URL}/equities/bars/daily",
                headers=HEADERS,
                params=params,
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                records = (
                    data.get("data")
                    or data.get("daily_quotes")
                    or data.get("bars")
                    or []
                )
                return records
            elif resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"  ⏳ レートリミット → {wait}秒待機...")
                time.sleep(wait)
            elif resp.status_code == 404:
                print(f"  📭 {target_date}: データなし（休日）")
                return []
            else:
                print(
                    f"  ❌ {target_date}: {resp.status_code} {resp.text[:100]}"
                )
                return []
        except Exception as e:
            print(f"  ⚠️ 例外: {e}")
            time.sleep(5)
    return []


# ─────────────────────────────────────────
# 4. メイン処理
# ─────────────────────────────────────────
def main():
    print("=" * 60)
    print("🚀 高速差分データ取得開始（日付ごと全銘柄一括）")
    print("=" * 60)

    # 既存データ読み込み
    csv_path, existing_df = get_latest_csv()
    last_date = get_last_date(existing_df)

    # 取得期間の設定
    today = date.today()

    if last_date is None:
        # 初回取得: 直近90日
        start_date = today - timedelta(days=90)
        print(f"📌 初回取得: {start_date} 〜 {today}")
    else:
        start_date = last_date + timedelta(days=1)
        if start_date > today:
            print("✅ 既に最新データです。取得不要。")
            return
        print(f"📌 差分取得: {start_date} 〜 {today}")

    # 営業日リスト取得
    trading_days = get_trading_days(start_date, today)

    if not trading_days:
        print("📭 取得対象の営業日がありません。")
        return

    print(f"\n⚡ APIコール数: {len(trading_days)}回（最大）")
    print(f"⏱️  推定時間: 約{len(trading_days) * 1}〜{len(trading_days) * 2}秒")
    print("-" * 60)

    # 全日付のデータを取得
    all_new_records = []
    for i, td in enumerate(trading_days):
        print(
            f"  [{i+1}/{len(trading_days)}] {td} 取得中...", end="", flush=True
        )
        records = fetch_one_day(td)
        if records:
            all_new_records.extend(records)
            print(f" → {len(records)}件")
        else:
            print(" → データなし")
        time.sleep(0.3)

    if not all_new_records:
        print("\n📭 新規データなし。")
        return

    # DataFrameに変換
    new_df = pd.DataFrame(all_new_records)
    new_df["Date"] = pd.to_datetime(new_df["Date"]).dt.strftime("%Y-%m-%d")
    new_df["Code"] = new_df["Code"].astype(str).str.strip()

    print(f"\n✅ 新規取得: {len(new_df):,}件")

    # 既存データと結合（UnboundLocalErrorの修正箇所）
    if existing_df is not None and not existing_df.empty:
        existing_df["Date"] = pd.to_datetime(existing_df["Date"]).dt.strftime(
            "%Y-%m-%d"
        )
        existing_df["Code"] = existing_df["Code"].astype(str).str.strip()

        # 列構成を統一
        all_cols = list(existing_df.columns)
        for col in all_cols:
            if col not in new_df.columns:
                new_df[col] = np.nan
        new_df = new_df[all_cols]

        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    # 重複排除・ソート
    combined_df.dropna(axis=1, how="all", inplace=True)
    combined_df.drop_duplicates(
        subset=["Date", "Code"], keep="last", inplace=True
    )
    combined_df.sort_values(["Code", "Date"], inplace=True)

    # 保存ファイル名決定
    min_date = (
        pd.to_datetime(combined_df["Date"])
        .min()
        .strftime("%Y%m%d")
        .replace("-", "")
    )
    max_date = (
        pd.to_datetime(combined_df["Date"])
        .max()
        .strftime("%Y%m%d")
        .replace("-", "")
    )
    today_str = today.strftime("%Y%m%d")
    new_filename = f"stocks_OHLC_{min_date}_{max_date}_{today_str}_fixed.csv"
    new_path = os.path.join(SAVE_DIR, new_filename)

    combined_df.to_csv(new_path, index=False, encoding="utf-8-sig")

    print(f"\n💾 保存完了: {new_filename}")
    print(f"   総レコード数: {len(combined_df):,}件")
    print(f"   期間: {combined_df['Date'].min()} 〜 {combined_df['Date'].max()}")
    print("=" * 60)


if __name__ == "__main__":
    main()