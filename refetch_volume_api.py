# refetch_volume_api.py を以下の内容で上書き保存

import pandas as pd
import requests
import time

API_KEY  = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL = "https://api.jquants.com"
CSV_IN   = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"
CSV_OUT  = r"C:\stock_system\stocks_OHLC_20260515_20260818_complete.csv"

HEADERS = {"x-api-key": API_KEY}

def fetch_bars(code, date_from, date_to):
    url = f"{BASE_URL}/equities/bars/daily"
    params = {"code": code, "date_from": date_from, "date_to": date_to}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            key = next((k for k in data if isinstance(data[k], list)), None)
            if key:
                return pd.DataFrame(data[key])
        else:
            print(f"  ⚠️ {code} → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {code} → {e}")
    return pd.DataFrame()

# ─────────────────────────────────────────
print("📂 データ読み込み中...")
df = pd.read_csv(CSV_IN, dtype={"Code": str}, low_memory=False)
df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
print(f"  総行数: {len(df):,}")

missing_mask  = df["Volume"].isna()
missing_codes = df[missing_mask]["Code"].unique()
print(f"  Volume欠損銘柄数: {len(missing_codes):,}")
print(f"  Volume欠損行数:   {missing_mask.sum():,}")

# ─────────────────────────────────────────
print("\n🔄 API取得 & 補完中...")
filled_total = 0
error_codes  = []

for i, code in enumerate(missing_codes):
    if i % 100 == 0:
        print(f"  進捗: {i:,}/{len(missing_codes):,} 銘柄 (補完済: {filled_total:,}行)")

    code_mask  = missing_mask & (df["Code"] == code)
    code_dates = df[code_mask]["Date"]
    c_from     = code_dates.min()
    c_to       = code_dates.max()

    api_df = fetch_bars(code, c_from, c_to)
    if api_df.empty:
        error_codes.append(code)
        continue

    # 列名を小文字で統一して確認
    api_df.columns = [c.strip() for c in api_df.columns]
    col_lower = {c.lower(): c for c in api_df.columns}

    # Date列を特定
    date_col = col_lower.get("date") or col_lower.get("tradingdate")
    if date_col is None:
        error_codes.append(code)
        continue
    api_df["Date"] = pd.to_datetime(api_df[date_col]).dt.strftime("%Y-%m-%d")

    # Volume列を特定
    vol_col = (col_lower.get("volume") or col_lower.get("vo")
               or col_lower.get("turnovervolume"))
    if vol_col is None:
        error_codes.append(code)
        continue

    # インデックス化してマージ
    api_df["Code"] = str(code)
    api_map = api_df.set_index(["Code", "Date"])[vol_col]

    for idx in df[code_mask].index:
        key = (df.at[idx, "Code"], df.at[idx, "Date"])
        if key in api_map.index:
            df.at[idx, "Volume"] = api_map[key]
            filled_total += 1

    time.sleep(0.1)

# ─────────────────────────────────────────
print(f"\n✅ 補完完了!")
print(f"  補完成功行数: {filled_total:,}")
print(f"  残存欠損行数: {df['Volume'].isna().sum():,}")
print(f"  エラー銘柄数: {len(error_codes):,}")

df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
print(f"\n💾 保存完了: {CSV_OUT}")
print(f"   総行数: {len(df):,}")