import datetime
import glob
import os
import sys
import numpy as np
import pandas as pd
import requests

API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
API_BASE = "https://api.jquants.com/v2"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_CSV = os.path.join(DATA_DIR, "stocks_OHLC_latest.csv")

headers = {"x-api-key": API_KEY}

def get_existing_data():
    csv_files = glob.glob(os.path.join(DATA_DIR, "stocks_*.csv"))
    if not csv_files:
        csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

    target_csv = None
    for f in csv_files:
        if "stocks_OHLC_latest.csv" in f:
            continue
        if "stocks_" in os.path.basename(f):
            target_csv = f
            break
    if not target_csv and csv_files:
        target_csv = csv_files[0]

    if target_csv and os.path.exists(target_csv):
        try:
            df = pd.read_csv(target_csv, dtype=str)
            df["Date"] = pd.to_datetime(df["Date"])
            max_date = df["Date"].max().date()
            print(f"📂 既存データ検出: {os.path.basename(target_csv)} (最新日: {max_date})")
            return df, max_date, target_csv
        except Exception as e:
            print(f"⚠️ 既存ファイル読み込みスキップ: {e}")
    return None, None, LATEST_CSV

def fetch_master():
    url = f"{API_BASE}/equities/master"
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("data") or data.get("master") or []
        df_m = pd.DataFrame(items)
        if not df_m.empty and "Code" in df_m.columns:
            df_m["Code"] = df_m["Code"].astype(str).str.strip()
            df_m["Code_4"] = df_m["Code"].apply(lambda x: str(x)[:4] if len(str(x)) >= 4 else str(x))
            
            rename_dict = {
                "CoName": "Name",
                "CoNameEn": "NameEn",
                "MktNm": "Market",
                "S33Nm": "Sector",
                "ScaleCat": "Scale"
            }
            df_m = df_m.rename(columns=rename_dict)
            return df_m
    return pd.DataFrame()

def fetch_financial_summary(days_back=130):
    url = f"{API_BASE}/fins/summary"
    all_fins = []
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_back)
    
    print(f"💹 財務データ取得中（開示期間: {start_date} ～ {today}）...")
    cur_date = start_date
    while cur_date <= today:
        if cur_date.weekday() < 5:
            date_str = cur_date.strftime("%Y-%m-%d")
            params = {"date": date_str}
            while True:
                try:
                    resp = requests.get(url, headers=headers, params=params, timeout=20)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("data") or data.get("fins_summary") or data.get("summary") or []
                        if items:
                            all_fins.extend(items)
                        pagination_key = data.get("pagination_key")
                        if not pagination_key:
                            break
                        params["pagination_key"] = pagination_key
                    else:
                        break
                except Exception:
                    break
        cur_date += datetime.timedelta(days=1)

    target_cols = ["BPS", "EPS", "FEPS", "NxFEPS"]
    if not all_fins:
        print("⚠️ 財務データが開示期間内に見つかりませんでした。")
        return pd.DataFrame(columns=["Code_4"] + target_cols)

    df_fin = pd.DataFrame(all_fins)
    if "Code" not in df_fin.columns:
        return pd.DataFrame(columns=["Code_4"] + target_cols)

    df_fin["Code"] = df_fin["Code"].astype(str).str.strip()
    df_fin["Code_4"] = df_fin["Code"].apply(lambda x: str(x)[:4] if len(str(x)) >= 4 else str(x))

    date_col = "DiscDate" if "DiscDate" in df_fin.columns else "DisclosedDate" if "DisclosedDate" in df_fin.columns else "CurPerEn"
    if date_col in df_fin.columns:
        df_fin = df_fin.sort_values(["Code_4", date_col])

    for col in target_cols:
        if col in df_fin.columns:
            df_fin[col] = df_fin[col].replace(["", "None", "null", "-", "－"], np.nan)
            df_fin[col] = pd.to_numeric(df_fin[col], errors="coerce")
        else:
            df_fin[col] = np.nan

    def get_last_valid(series):
        valid = series.dropna()
        return valid.iloc[-1] if not valid.empty else np.nan

    fin_agg = df_fin.groupby("Code_4")[target_cols].agg(get_last_valid).reset_index()
    
    # FEPSが未開示の場合は直近のEPSを採用して補完
    fin_agg["FEPS"] = fin_agg["FEPS"].fillna(fin_agg["EPS"])
    
    return fin_agg

def fetch_daily_quotes_range(start_date, end_date):
    url = f"{API_BASE}/equities/bars/daily"
    all_quotes = []

    cur_date = start_date
    while cur_date <= end_date:
        if cur_date.weekday() < 5:
            date_str = cur_date.strftime("%Y-%m-%d")
            params = {"date": date_str}
            
            while True:
                resp = requests.get(url, headers=headers, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    quotes = data.get("data") or data.get("bars") or data.get("daily_bars") or data.get("daily_quotes") or []
                    if quotes:
                        all_quotes.extend(quotes)
                    
                    pagination_key = data.get("pagination_key")
                    if not pagination_key:
                        break
                    params["pagination_key"] = pagination_key
                else:
                    break
        cur_date += datetime.timedelta(days=1)

    if not all_quotes:
        return pd.DataFrame()

    df_q = pd.DataFrame(all_quotes)
    col_rename = {
        "AdjustmentOpen": "AdjO", "AdjustmentHigh": "AdjH", "AdjustmentLow": "AdjL", "AdjustmentClose": "AdjC",
        "AdjustmentVolume": "AdjVo", "Open": "Open", "High": "High", "Low": "Low", "Close": "Close", "Volume": "Volume"
    }
    df_q = df_q.rename(columns=col_rename)
    if "Date" in df_q.columns:
        df_q["Date"] = pd.to_datetime(df_q["Date"])
    if "Code" in df_q.columns:
        df_q["Code"] = df_q["Code"].astype(str).str.strip()
        df_q["Code_4"] = df_q["Code"].apply(lambda x: str(x)[:4] if len(str(x)) >= 4 else str(x))
    return df_q

def main():
    today = datetime.date.today()
    existing_df, max_date, save_path = get_existing_data()

    if max_date is not None:
        start_date = max_date + datetime.timedelta(days=1)
        if start_date <= today:
            print(f"⚡ 差分更新を開始: {start_date} ～ {today}")
            new_quotes = fetch_daily_quotes_range(start_date, today)
        else:
            print("✅ 株価データは最新です。マスタ・財務情報を再結合します。")
            new_quotes = pd.DataFrame()
    else:
        start_date = today - datetime.timedelta(days=60)
        print(f"🚀 新規データ一括取得: {start_date} ～ {today}")
        new_quotes = fetch_daily_quotes_range(start_date, today)

    # 1. 株価統合
    if not new_quotes.empty:
        if existing_df is not None and not existing_df.empty:
            merged_df = pd.concat([existing_df, new_quotes], ignore_index=True)
        else:
            merged_df = new_quotes
    else:
        merged_df = existing_df if existing_df is not None else pd.DataFrame()

    if merged_df.empty:
        print("⚠️ データが存在しません。")
        return

    merged_df["Code"] = merged_df["Code"].astype(str).str.strip()
    merged_df["Code_4"] = merged_df["Code"].apply(lambda x: str(x)[:4] if len(str(x)) >= 4 else str(x))
    merged_df = merged_df.drop_duplicates(subset=["Code", "Date"], keep="last")
    merged_df = merged_df.sort_values(["Code", "Date"]).reset_index(drop=True)

    # クリーンアップ
    cleanup_cols = ["Name", "Market", "Sector", "BPS", "EPS", "FEPS", "NxFEPS"]
    merged_df = merged_df.drop(columns=[c for c in cleanup_cols if c in merged_df.columns], errors="ignore")

    # 2. マスタ結合
    print("🏛️ 銘柄マスタ（社名・業種・市場）を結合中...")
    master_df = fetch_master()
    if not master_df.empty:
        master_df["Code_4"] = master_df["Code_4"].astype(str).str.strip()
        m_cols = [c for c in ["Code_4", "Name", "Market", "Sector"] if c in master_df.columns]
        merged_df = pd.merge(merged_df, master_df[m_cols].drop_duplicates(subset=["Code_4"]), on="Code_4", how="left")

    # 3. 財務結合
    fin_df = fetch_financial_summary()
    if not fin_df.empty:
        fin_df["Code_4"] = fin_df["Code_4"].astype(str).str.strip()
        merged_df = pd.merge(merged_df, fin_df, on="Code_4", how="left")

    for c in ["Name", "Market", "Sector", "BPS", "EPS", "FEPS", "NxFEPS"]:
        if c not in merged_df.columns:
            merged_df[c] = np.nan

    # 4. 保存
    target_save_path = os.path.join(DATA_DIR, "stocks_OHLC_latest.csv")
    merged_df.to_csv(target_save_path, index=False, encoding="utf-8-sig")
    print(f"🎉 結合完了！ 保存先: {os.path.basename(target_save_path)}")
    print(f"📊 社名件数: {merged_df['Name'].notna().sum():,} | BPS件数: {merged_df['BPS'].notna().sum():,} | FEPS件数: {merged_df['FEPS'].notna().sum():,}")

if __name__ == "__main__":
    main()