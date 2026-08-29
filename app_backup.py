import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import subprocess
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===== 設定 =====
API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
API_BASE = "https://api.jquants.com/v2"
VENV_PYTHON = r"C:\stock_system\venv\Scripts\python.exe"
DATA_DIR = r"C:\stock_system"

st.set_page_config(page_title="株式分析システム", layout="wide", page_icon="📈")

# ===== CSS =====
st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 4px 0;
    border-left: 4px solid #7c3aed;
}
.step-header {
    background: linear-gradient(90deg, #7c3aed22, transparent);
    border-left: 4px solid #7c3aed;
    padding: 8px 16px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0 8px 0;
}
.positive { color: #ef4444; }
.negative { color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# ===== ユーティリティ関数 =====

@st.cache_data
def get_csv_files():
    files = glob.glob(os.path.join(DATA_DIR, "stocks_OHLC_*.csv"))
    files.sort(key=os.path.getmtime, reverse=True)
    return files

@st.cache_data
def load_csv(filepath):
    df = pd.read_csv(filepath, dtype={"Code": str})
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def calc_ma(series, period):
    return series.rolling(period).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal).mean()
    hist = macd - sig
    return macd, sig, hist

def calc_bollinger(series, period=20, std_mult=2):
    ma = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    return ma + std_mult * sigma, ma, ma - std_mult * sigma

def calc_stoch(df, k=14, d=3):
    low_min = df["AdjL"].rolling(k).min()
    high_max = df["AdjH"].rolling(k).max()
    k_line = 100 * (df["AdjC"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d_line = k_line.rolling(d).mean()
    return k_line, d_line

# ===== スクリーニング =====

def run_screening(df, params):
    latest_date = df["Date"].max()
    latest = df[df["Date"] == latest_date].copy()

    if params.get("vol_min"):
        latest = latest[latest["AdjVo"] >= params["vol_min"]]
    if params.get("mktcap_min"):
        latest = latest[latest["MktCap"] >= params["mktcap_min"]]

    results = []
    for code in latest["Code"].unique():
        stock_df = df[df["Code"] == code].sort_values("Date").tail(80)
        if len(stock_df) < 25:
            continue

        row = latest[latest["Code"] == code].iloc[0]
        price = row["AdjC"]
        adj = stock_df["AdjC"]

        ma5  = calc_ma(adj, 5).iloc[-1]
        ma25 = calc_ma(adj, 25).iloc[-1]
        ma75 = calc_ma(adj, 75).iloc[-1] if len(stock_df) >= 75 else None

        # MAフィルタ
        if params.get("ma5_above_ma25") and not (ma5 > ma25):
            continue
        if params.get("ma25_above_ma75") and ma75 is not None and not (ma25 > ma75):
            continue

        rsi_val = calc_rsi(adj).iloc[-1]
        if params.get("rsi_min") and not np.isnan(rsi_val) and rsi_val < params["rsi_min"]:
            continue
        if params.get("rsi_max") and not np.isnan(rsi_val) and rsi_val > params["rsi_max"]:
            continue

        # 前日比
        if len(stock_df) >= 2:
            prev_close = stock_df["AdjC"].iloc[-2]
            chg_pct = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
        else:
            chg_pct = 0

        results.append({
            "Code": code,
            "Name": row.get("Name", ""),
            "Sector": row.get("Sector", ""),
            "Close": round(price, 1),
            "前日比(%)": round(chg_pct, 2),
            "Volume": int(row["AdjVo"]),
            "MktCap(百万)": round(row.get("MktCap", 0), 0),
            "MA5": round(ma5, 1),
            "MA25": round(ma25, 1),
            "RSI": round(rsi_val, 1) if not np.isnan(rsi_val) else None,
        })

    return pd.DataFrame(results)

# ===== バックテスト =====

def run_backtest(df, code, sp):
    stock_df = df[df["Code"] == code].sort_values("Date").copy().reset_index(drop=True)
    if len(stock_df) < 30:
        return None, None, stock_df

    adj = stock_df["AdjC"]
    stock_df["MA5"]    = calc_ma(adj, 5)
    stock_df["MA25"]   = calc_ma(adj, 25)
    stock_df["RSI"]    = calc_rsi(adj)
    macd, sig, hist    = calc_macd(adj)
    stock_df["MACD"]   = macd
    stock_df["Signal"] = sig
    stock_df["Hist"]   = hist

    trades = []
    position = None
    capital = sp.get("capital", 1_000_000)
    initial = capital

    for i in range(26, len(stock_df)):
        row  = stock_df.iloc[i]
        prev = stock_df.iloc[i - 1]
        buy_sig = sell_sig = False

        # エントリーシグナル
        if sp.get("entry_ma"):
            if prev["MA5"] <= prev["MA25"] and row["MA5"] > row["MA25"]:
                buy_sig = True
        if sp.get("entry_rsi"):
            if not np.isnan(row["RSI"]) and row["RSI"] < sp.get("rsi_entry", 30):
                buy_sig = True
        if sp.get("entry_macd"):
            if prev["MACD"] <= prev["Signal"] and row["MACD"] > row["Signal"]:
                buy_sig = True

        # エグジットシグナル
        if position:
            chg = (row["AdjC"] - position["entry_price"]) / position["entry_price"]
            if chg >= sp.get("take_profit", 0.10):
                sell_sig = True
            if chg <= -sp.get("stop_loss", 0.05):
                sell_sig = True
            if sp.get("exit_ma"):
                if prev["MA5"] >= prev["MA25"] and row["MA5"] < row["MA25"]:
                    sell_sig = True

        if buy_sig and not position:
            shares = int(capital // row["AdjC"])
            if shares > 0:
                position = {
                    "entry_date": row["Date"],
                    "entry_price": row["AdjC"],
                    "shares": shares,
                }
                capital -= shares * row["AdjC"]

        elif sell_sig and position:
            profit = (row["AdjC"] - position["entry_price"]) * position["shares"]
            capital += position["shares"] * row["AdjC"]
            trades.append({
                "エントリー日": position["entry_date"],
                "エグジット日": row["Date"],
                "買値": position["entry_price"],
                "売値": row["AdjC"],
                "株数": position["shares"],
                "損益(円)": round(profit, 0),
                "リターン(%)": round((row["AdjC"] / position["entry_price"] - 1) * 100, 2),
            })
            position = None

    trades_df = pd.DataFrame(trades)
    summary = {}
    if not trades_df.empty:
        wins = trades_df[trades_df["損益(円)"] > 0]
        final = capital + (position["shares"] * stock_df.iloc[-1]["AdjC"] if position else 0)
        summary = {
            "総トレード数": len(trades_df),
            "勝率(%)": round(len(wins) / len(trades_df) * 100, 1),
            "総損益(円)": round(trades_df["損益(円)"].sum(), 0),
            "平均損益(円)": round(trades_df["損益(円)"].mean(), 0),
            "最大利益(円)": round(trades_df["損益(円)"].max(), 0),
            "最大損失(円)": round(trades_df["損益(円)"].min(), 0),
            "最終資本(円)": round(final, 0),
            "総リターン(%)": round((final - initial) / initial * 100, 2),
        }

    return trades_df, summary, stock_df

# ===== チャート作成 =====

def create_chart(stock_df, code, name, indicators, show_vol=True):
    subplot_rows = [("main", 0.50)]
    if show_vol:
        subplot_rows.append(("vol", 0.12))
    if "RSI" in indicators:
        subplot_rows.append(("rsi", 0.13))
    if "MACD" in indicators:
        subplot_rows.append(("macd", 0.15))
    if "STOCH" in indicators:
        subplot_rows.append(("stoch", 0.13))

    n_rows = len(subplot_rows)
    heights = [r[1] for r in subplot_rows]
    row_map = {r[0]: i + 1 for i, r in enumerate(subplot_rows)}

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        row_heights=heights,
        vertical_spacing=0.02,
    )

    # ローソク足
    fig.add_trace(go.Candlestick(
        x=stock_df["Date"],
        open=stock_df["AdjO"], high=stock_df["AdjH"],
        low=stock_df["AdjL"],  close=stock_df["AdjC"],
        name="価格",
        increasing_line_color="#ef4444",
        decreasing_line_color="#3b82f6",
    ), row=row_map["main"], col=1)

    adj = stock_df["AdjC"]

    if "MA5" in indicators:
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=calc_ma(adj, 5),
            name="MA5", line=dict(color="#f97316", width=1.5)),
            row=row_map["main"], col=1)
    if "MA25" in indicators:
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=calc_ma(adj, 25),
            name="MA25", line=dict(color="#06b6d4", width=1.5)),
            row=row_map["main"], col=1)
    if "MA75" in indicators:
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=calc_ma(adj, 75),
            name="MA75", line=dict(color="#84cc16", width=1.5)),
            row=row_map["main"], col=1)
    if "BB" in indicators:
        upper, mid, lower = calc_bollinger(adj)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=upper,
            name="BB上", line=dict(color="#a78bfa", dash="dash", width=1)),
            row=row_map["main"], col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=lower,
            name="BB下", line=dict(color="#a78bfa", dash="dash", width=1),
            fill="tonexty", fillcolor="rgba(167,139,250,0.08)"),
            row=row_map["main"], col=1)

    # 出来高
    if show_vol and "vol" in row_map:
        colors = ["#ef4444" if c >= o else "#3b82f6"
                  for c, o in zip(stock_df["AdjC"], stock_df["AdjO"])]
        fig.add_trace(go.Bar(
            x=stock_df["Date"], y=stock_df["AdjVo"],
            name="出来高", marker_color=colors, opacity=0.7),
            row=row_map["vol"], col=1)

    # RSI
    if "RSI" in indicators and "rsi" in row_map:
        rsi = calc_rsi(adj)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=rsi,
            name="RSI", line=dict(color="#c084fc", width=1.5)),
            row=row_map["rsi"], col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                      line_width=1, row=row_map["rsi"], col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#22c55e",
                      line_width=1, row=row_map["rsi"], col=1)
        fig.update_yaxes(range=[0, 100], row=row_map["rsi"], col=1)

    # MACD
    if "MACD" in indicators and "macd" in row_map:
        macd, sig, hist = calc_macd(adj)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=macd,
            name="MACD", line=dict(color="#60a5fa", width=1.5)),
            row=row_map["macd"], col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=sig,
            name="Signal", line=dict(color="#f87171", width=1.5)),
            row=row_map["macd"], col=1)
        bar_colors = ["#ef4444" if v >= 0 else "#3b82f6" for v in hist]
        fig.add_trace(go.Bar(x=stock_df["Date"], y=hist,
            name="Hist", marker_color=bar_colors, opacity=0.7),
            row=row_map["macd"], col=1)

    # ストキャスティクス
    if "STOCH" in indicators and "stoch" in row_map:
        k_line, d_line = calc_stoch(stock_df)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=k_line,
            name="%K", line=dict(color="#fbbf24", width=1.5)),
            row=row_map["stoch"], col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=d_line,
            name="%D", line=dict(color="#f472b6", width=1.5)),
            row=row_map["stoch"], col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="#ef4444",
                      line_width=1, row=row_map["stoch"], col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#22c55e",
                      line_width=1, row=row_map["stoch"], col=1)

    fig.update_layout(
        title=dict(text=f"<b>{code}</b>　{name}", font=dict(size=18)),
        height=300 + 150 * n_rows,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=40, r=40, t=60, b=20),
    )
    return fig

# ===== ファンダメンタルデータ取得 =====

def fetch_fundamental(code: str, current_price: float = 0) -> dict | None:
    """J-Quants /fins/summary からファンダメンタルデータを取得"""
    try:
        url = f"{API_BASE}/fins/summary"
        resp = requests.get(
            url,
            headers={"X-API-KEY": API_KEY},
            params={"code": code},
            timeout=10
        )
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        items = resp.json().get("data", [])
        if not items:
            return None

        # FY（通期）決算を優先、なければ最新を使用
        fy_items = [x for x in items if x.get("CurPerType") == "FY"]
        latest_fy  = fy_items[-1]  if fy_items  else None
        latest_any = items[-1]

        def _f(v):
            """文字列→float変換、空は None"""
            try:
                return float(v) if v not in ("", None) else None
            except Exception:
                return None

        # BPS/ROEはFYから優先取得
        eps = _f(latest_any.get("EPS"))
        bps = _f(latest_fy.get("BPS"))  if latest_fy else None
        roe = _f(latest_fy.get("ROE"))  if latest_fy else None

        # BPSがFYで空なら最新レコードからも試みる
        if bps is None:
            bps = _f(latest_any.get("BPS"))
        if roe is None:
            roe = _f(latest_any.get("ROE"))

        # 配当・予想
        f_div_ann = _f(latest_any.get("FDivAnn"))
        f_eps     = _f(latest_any.get("FEPS"))
        div_ann   = _f(latest_fy.get("DivAnn")) if latest_fy else None
        eq_ar     = _f(latest_any.get("EqAR"))

        # PER / PBR 計算
        per = round(current_price / eps, 2)  if (eps and eps > 0 and current_price > 0) else None
        pbr = round(current_price / bps, 2)  if (bps and bps > 0 and current_price > 0) else None

        # 配当利回り
        div_yield = None
        if f_div_ann and f_div_ann > 0 and current_price > 0:
            div_yield = round(f_div_ann / current_price * 100, 2)
        elif div_ann and div_ann > 0 and current_price > 0:
            div_yield = round(div_ann / current_price * 100, 2)

        # 業績（直近FY）
        sales = _f(latest_fy.get("Sales")) if latest_fy else None
        op    = _f(latest_fy.get("OP"))    if latest_fy else None
        np_   = _f(latest_fy.get("NP"))    if latest_fy else None
        cfo   = _f(latest_fy.get("CFO"))   if latest_fy else None

        def _fmt_oku(v):
            """円→億円表示"""
            if v is None:
                return None
            return round(v / 1e8, 1)

        return {
            "PER(倍)":      f"{per:.1f}" if per else "N/A",
            "PBR(倍)":      f"{pbr:.2f}" if pbr else "N/A",
            "ROE(%)":       f"{roe*100:.1f}" if roe else "N/A",
            "配当利回り(%)": f"{div_yield:.2f}" if div_yield else "N/A",
            "EPS(円)":      f"{eps:.2f}"  if eps else "N/A",
            "BPS(円)":      f"{bps:.2f}"  if bps else "N/A",
            # 業績
            "売上高(億円)":   _fmt_oku(sales),
            "営業利益(億円)": _fmt_oku(op),
            "純利益(億円)":   _fmt_oku(np_),
            "営業CF(億円)":   _fmt_oku(cfo),
            # 予想
            "予想EPS(円)":    f"{f_eps:.2f}"     if f_eps    else "N/A",
            "予想配当(円)":   f"{f_div_ann:.1f}" if f_div_ann else "N/A",
            "自己資本比率(%)":f"{eq_ar*100:.1f}" if eq_ar    else "N/A",
            # メタ
            "_per_raw": per,
            "_pbr_raw": pbr,
            "_disc_date": latest_any.get("DiscDate", ""),
            "_fy_date":   latest_fy.get("CurFYEn", "") if latest_fy else "",
        }
    except Exception as e:
        return {"error": str(e)}




def show_fundamental_section(selected_code: str, selected_name: str, current_price: float):
    """ファンダメンタル分析セクションの表示"""
    st.markdown("---")
    st.subheader(f"📊 ファンダメンタル分析：{selected_name}（{selected_code}）")

    with st.spinner("ファンダメンタルデータ取得中..."):
        fd = fetch_fundamental(selected_code, current_price)

    if fd is None:
        st.warning("⚠️ データが取得できませんでした")
        return

    if "error" in fd:
        st.error(f"❌ エラー: {fd['error']}")
        return

    # メタ情報
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.caption(f"📅 最新開示日: {fd.get('_disc_date', 'N/A')}")
    with col_m2:
        st.caption(f"📅 FY決算期末: {fd.get('_fy_date', 'N/A')}")

    # バリュエーション
    st.markdown("#### 💹 バリュエーション")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PER（倍）",    fd.get("PER(倍)",       "N/A"), help="株価収益率")
    c2.metric("PBR（倍）",    fd.get("PBR(倍)",       "N/A"), help="株価純資産倍率")
    c3.metric("ROE（%）",     fd.get("ROE(%)",        "N/A"), help="自己資本利益率")
    c4.metric("配当利回り（%）", fd.get("配当利回り(%)", "N/A"), help="予想配当利回り")

    # 1株指標
    st.markdown("#### 📌 1株指標")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("EPS（円）",     fd.get("EPS(円)",      "N/A"), help="1株当たり利益")
    c6.metric("BPS（円）",     fd.get("BPS(円)",      "N/A"), help="1株当たり純資産")
    c7.metric("予想EPS（円）",  fd.get("予想EPS(円)",  "N/A"), help="通期予想EPS")
    c8.metric("予想配当（円）",  fd.get("予想配当(円)", "N/A"), help="通期予想配当")

    # 業績（億円）
    st.markdown("#### 🏢 業績（直近FY・億円）")
    c9, c10, c11, c12 = st.columns(4)
    c9.metric("売上高",    fd.get("売上高(億円)",   "N/A"))
    c10.metric("営業利益", fd.get("営業利益(億円)", "N/A"))
    c11.metric("純利益",   fd.get("純利益(億円)",   "N/A"))
    c12.metric("営業CF",   fd.get("営業CF(億円)",   "N/A"))

    # 財務健全性
    st.markdown("#### 🛡️ 財務健全性")
    c13, c14, c15, c16 = st.columns(4)
    c13.metric("自己資本比率（%）", fd.get("自己資本比率(%)", "N/A"))
    c14.metric("", "")
    c15.metric("", "")
    c16.metric("", "")

