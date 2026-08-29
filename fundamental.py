# C:\stock_system\fundamental.py
"""
J-Quants API V2 から財務サマリーを取得・整形するモジュール
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
BASE_URL = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}


def fetch_fins_summary(code: str) -> pd.DataFrame:
    """
    指定銘柄の財務サマリーを取得して整形済みDataFrameを返す
    
    Parameters
    ----------
    code : str  例 "7203" または "72030"
    
    Returns
    -------
    pd.DataFrame  最新順にソートされた財務データ
    """
    # コードの末尾0補完（J-Quantsは5桁）
    if len(code) == 4:
        code_5 = code + "0"
    else:
        code_5 = code

    r = requests.get(
        f"{BASE_URL}/fins/summary",
        headers=HEADERS,
        params={"code": code_5}
    )
    
    if r.status_code != 200:
        return pd.DataFrame()
    
    data = r.json().get("data", [])
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # 日付・数値変換
    df["DiscDate"] = pd.to_datetime(df["DiscDate"])
    df = df.sort_values("DiscDate", ascending=False).reset_index(drop=True)
    
    # 数値カラムを変換
    numeric_cols = [
        "Sales", "OP", "NP", "EPS", "DEPS", "TA", "Eq", "EqAR", "BPS",
        "CFO", "CFI", "CFF", "CashEq",
        "FSales", "FOP", "FNP", "FEPS",
        "Div2Q", "DivFY", "DivAnn",
        "ShOutFY", "TrShFY", "AvgSh"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df


def get_latest_financials(code: str) -> dict:
    """
    最新の財務情報を辞書形式で返す（Streamlit表示用）
    """
    df = fetch_fins_summary(code)
    if df.empty:
        return {}
    
    # 最新の通期決算を優先
    annual = df[df["DocType"].str.contains("Annual|FY|通期", na=False, case=False)]
    latest = annual.iloc[0] if not annual.empty else df.iloc[0]
    
    # 単位変換（億円）
    def to_oku(val):
        try:
            return round(float(val) / 1e8, 1) if val and str(val) != "nan" else None
        except:
            return None
    
    result = {
        "開示日": latest.get("DiscDate", ""),
        "決算種別": latest.get("DocType", ""),
        "対象期間": f"{latest.get('CurPerSt','')} ～ {latest.get('CurPerEn','')}",
        "売上高(億円)": to_oku(latest.get("Sales")),
        "営業利益(億円)": to_oku(latest.get("OP")),
        "純利益(億円)": to_oku(latest.get("NP")),
        "EPS(円)": latest.get("EPS"),
        "BPS(円)": latest.get("BPS"),
        "自己資本比率(%)": round(float(latest["EqAR"]) * 100, 1) if pd.notna(latest.get("EqAR")) else None,
        "総資産(億円)": to_oku(latest.get("TA")),
        "自己資本(億円)": to_oku(latest.get("Eq")),
        "営業CF(億円)": to_oku(latest.get("CFO")),
        "投資CF(億円)": to_oku(latest.get("CFI")),
        "財務CF(億円)": to_oku(latest.get("CFF")),
        "現金等(億円)": to_oku(latest.get("CashEq")),
        "配当(円/株)": latest.get("DivAnn") or latest.get("DivFY"),
        "予想売上高(億円)": to_oku(latest.get("FSales")),
        "予想営業利益(億円)": to_oku(latest.get("FOP")),
        "予想純利益(億円)": to_oku(latest.get("FNP")),
        "予想EPS(円)": latest.get("FEPS"),
    }
    
    return result


def get_fins_history_table(code: str, max_rows: int = 8) -> pd.DataFrame:
    """
    財務履歴を表形式で返す（直近N期分）
    """
    df = fetch_fins_summary(code)
    if df.empty:
        return pd.DataFrame()
    
    display_cols = {
        "DiscDate": "開示日",
        "CurPerType": "種別",
        "Sales": "売上高",
        "OP": "営業利益",
        "NP": "純利益",
        "EPS": "EPS",
        "EqAR": "自己資本比率",
        "DivAnn": "配当"
    }
    
    df_disp = df[[c for c in display_cols if c in df.columns]].copy()
    df_disp = df_disp.rename(columns=display_cols)
    
    # 億円変換
    for col in ["売上高", "営業利益", "純利益"]:
        if col in df_disp.columns:
            df_disp[col] = (df_disp[col] / 1e8).round(1).astype(str) + "億"
    
    if "自己資本比率" in df_disp.columns:
        df_disp["自己資本比率"] = (df_disp["自己資本比率"] * 100).round(1).astype(str) + "%"
    
    return df_disp.head(max_rows)