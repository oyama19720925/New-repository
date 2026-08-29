# C:\stock_system\update_db.py
"""
J-Quants API V2 を使用してローカルCSVを差分更新するスクリプト
equities/bars/daily + markets/calendar + equities/master 使用
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
BASE_URL = "https://api.jquants.com/v2"
HEADERS  = {"x-api-key": API_KEY}
CSV_PATH = r"C:\stock_system\stocks_OHLC_20260515_20260813_merged.csv"

# APIカラム → CSVカラム のリネームマップ
RENAME_MAP = {
    "O":  "Open",
    "H":  "High",
    "L":  "Low",
    "C":  "Close",
    "Vo": "Volume",
}


def fetch_trading_days(from_date: str, to_date: str) -> list:
    """カレンダーAPIから営業日（HolDiv='1'）のリストを返す"""
    r = requests.get(
        f"{BASE_URL}/markets/calendar",
        headers=HEADERS,
        params={"from": from_date, "to": to_date}
    )
    if r.status_code != 200:
        print(f"   ⚠️ カレンダーAPI エラー: {r.status_code}")
        return []
    data = r.json().get("data", [])
    return sorted([
        d["Date"] for d in data
        if str(d.get("HolDiv", "0")) == "1"
    ])


def fetch_daily_bars(date_str: str) -> list | None:
    """指定日の全銘柄株価を取得（403はNoneを返す）"""
    r = requests.get(
        f"{BASE_URL}/equities/bars/daily",
        headers=HEADERS,
        params={"date": date_str}
    )
    if r.status_code == 200:
        return r.json().get("data", [])
    elif r.status_code == 403:
        print(f"\n   🚫 403 Forbidden: {date_str} はアクセス不可")
        return None
    else:
        print(f"\n   ⚠️ APIエラー {date_str}: {r.status_code} - {r.text[:100]}")
        return []


def fetch_master() -> pd.DataFrame:
    """銘柄マスタを取得してCode/Name/Sector/Marketを返す"""
    r = requests.get(f"{BASE_URL}/equities/master", headers=HEADERS)
    if r.status_code != 200:
        print(f"   ⚠️ マスタAPI エラー: {r.status_code}")
        return pd.DataFrame()

    df = pd.DataFrame(r.json().get("data", []))
    if df.empty:
        return df

    # カラム名確認してリネーム
    print(f"   マスタカラム: {list(df.columns)}")
    rename = {}
    for api_col, csv_col in [("CoName","Name"), ("S33Nm","Sector"), ("MktNm","Market")]:
        if api_col in df.columns:
            rename[api_col] = csv_col
    df = df.rename(columns=rename)

    keep = [c for c in ["Code","Name","Sector","Market"] if c in df.columns]
    return df[keep].drop_duplicates("Code")


def update_csv():
    print("=" * 60)
    print("🔄 株価データ差分更新開始")
    print("=" * 60)

    # ── 既存CSV読み込み ──────────────────────────────────
    if os.path.exists(CSV_PATH):
        df_existing = pd.read_csv(CSV_PATH, low_memory=False)
        df_existing["Date"] = pd.to_datetime(df_existing["Date"])
        last_date = df_existing["Date"].max()
        print(f"📂 既存データ: {len(df_existing):,}行")
        print(f"   最終日付  : {last_date.strftime('%Y-%m-%d')}")
    else:
        df_existing = pd.DataFrame()
        last_date = datetime(2020, 1, 1)
        print("📂 既存データなし → 2020年以降を全取得")

    # ── 取得期間の設定 ───────────────────────────────────
    from_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    to_date   = datetime.now().strftime("%Y-%m-%d")

    print(f"\n📅 取得期間: {from_date} ～ {to_date}")

    if from_date > to_date:
        print("✅ 既に最新です。更新不要。")
        return

    # ── カレンダーから営業日取得 ─────────────────────────
    print("\n📆 営業日カレンダー取得中...")
    trading_days = fetch_trading_days(from_date, to_date)

    if not trading_days:
        print("✅ 取得すべき営業日なし。既に最新です。")
        return

    print(f"   対象営業日: {len(trading_days)}日")
    for d in trading_days:
        print(f"   　📅 {d}")

    # ── 銘柄マスタ取得 ───────────────────────────────────
    print("\n📋 銘柄マスタ取得中...")
    df_master = fetch_master()
    if not df_master.empty:
        print(f"   ✅ {len(df_master):,}銘柄")
    else:
        print("   ⚠️ マスタ取得失敗（Name/Sector/Marketなしで続行）")

    # ── 日付ごとにデータ取得 ─────────────────────────────
    new_records = []
    total = len(trading_days)

    for i, date_str in enumerate(trading_days):
        print(f"   [{i+1:2d}/{total}] {date_str} 取得中...", end="", flush=True)
        bars = fetch_daily_bars(date_str)

        if bars is None:
            print("\n🚫 403エラーのため処理中断")
            break
        elif bars:
            # カラムリネーム
            for rec in bars:
                for api_col, csv_col in RENAME_MAP.items():
                    if api_col in rec:
                        rec[csv_col] = rec.pop(api_col)
            new_records.extend(bars)
            print(f" ✅ {len(bars):,}件")
        else:
            print(f" ⚠️ 0件")

        time.sleep(0.3)  # API負荷対策

    if not new_records:
        print("\n✅ 新規データなし。更新不要。")
        return

    # ── 新規データ整形 ───────────────────────────────────
    df_new = pd.DataFrame(new_records)
    print(f"\n📊 新規取得合計: {len(df_new):,}行")

    # マスタ情報をマージ（Name/Sector/Market付与）
    if not df_master.empty and "Code" in df_new.columns:
        df_new["Code"] = df_new["Code"].astype(str)
        df_master["Code"] = df_master["Code"].astype(str)
        df_new = df_new.merge(df_master, on="Code", how="left")
        print(f"   ✅ 銘柄情報マージ完了")

    # ── 既存データと結合 ─────────────────────────────────
  if not df_existing.empty:
    all_cols = list(df_existing.columns)
    
    for c in all_cols:
        if c not in df_new.columns:
            df_new[c] = None

    # ⬇️ 修正：空列を除外してからconcat
    df_new_aligned = df_new[all_cols].copy()
    
    # 全NA列を事前に型変換してWarning回避
    for c in all_cols:
        if df_new_aligned[c].isna().all():
            df_new_aligned[c] = df_new_aligned[c].astype(
                df_existing[c].dtype if c in df_existing.columns else "object"
            )
    
    df_combined = pd.concat(
        [df_existing, df_new_aligned],
        ignore_index=True
    )
else:
    df_combined = df_new

    # ── 重複除去・ソート ─────────────────────────────────
    df_combined["Date"] = pd.to_datetime(df_combined["Date"])
    before = len(df_combined)
    df_combined = df_combined.drop_duplicates(subset=["Date","Code"])
    after  = len(df_combined)
    if before != after:
        print(f"   🗑️ 重複除去: {before - after}行削除")

    df_combined = df_combined.sort_values(["Date","Code"]).reset_index(drop=True)

    # ── 保存 ─────────────────────────────────────────────
    date_min = df_combined["Date"].min().strftime("%Y%m%d")
    date_max = df_combined["Date"].max().strftime("%Y%m%d")
    new_name = f"stocks_OHLC_{date_min}_{date_max}_merged.csv"
    new_path = os.path.join(os.path.dirname(CSV_PATH), new_name)

    df_combined.to_csv(new_path, index=False, encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"✅ 更新完了！")
    print(f"   総レコード数 : {len(df_combined):,}行")
    print(f"   期間         : {date_min} ～ {date_max}")
    print(f"   保存先       : {new_path}")
    print(f"{'='*60}")

    # 旧ファイルの削除確認
    if new_path != CSV_PATH and os.path.exists(CSV_PATH):
        ans = input(f"\n🗑️ 旧ファイルを削除しますか？ [y/N]: ").strip().lower()
        if ans == "y":
            os.remove(CSV_PATH)
            print(f"   ✅ 削除完了: {CSV_PATH}")
        else:
            print(f"   📂 旧ファイルは保持されます")


if __name__ == "__main__":
    update_csv()