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
            "MktCap(百万)": round(row.get("MktCap", 0) / 1e6, 0),
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

def fetch_fundamental(code, current_price):
    headers = {"X-API-KEY": API_KEY}
    url = f"{API_BASE}/fins/summary"
    try:
        resp = requests.get(url, headers=headers,
                            params={"code": code}, timeout=10)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        items = resp.json().get("fins_summary", [])
        if not items:
            return None
        item = items[-1]

        def f(k):
            v = item.get(k)
            try:
                return float(v) if v not in (None, "", "None") else 0.0
            except Exception:
                return 0.0

        eps  = f("EPS");  bps  = f("BPS");  roe  = f("ROE")
        sales = f("Sales"); op = f("OP");   np_  = f("NP")
        cfo  = f("CFO");  feps = f("FEPS"); fdiv = f("FDivAnn")

        per       = round(current_price / eps, 1) if eps > 0 else None
        pbr       = round(current_price / bps, 2) if bps > 0 else None
        div_yield = round(fdiv / current_price * 100, 2) \
                    if fdiv > 0 and current_price > 0 else None
        roe_pct   = round(roe * 100, 1) if 0 < roe < 1 else \
                    round(roe, 1) if roe != 0 else None

        return {
            "PER(倍)":       per,
            "PBR(倍)":       pbr,
            "ROE(%)":        roe_pct,
            "EPS(円)":       round(eps, 1)  if eps  else None,
            "BPS(円)":       round(bps, 1)  if bps  else None,
            "予想EPS(円)":   round(feps, 1) if feps else None,
            "配当利回り(%)": div_yield,
            "年間配当(円)":  fdiv if fdiv else None,
            "売上高(百万)":  round(sales / 1e6, 0) if sales > 0 else None,
            "営業利益(百万)": round(op / 1e6, 0)   if op    > 0 else None,
            "純利益(百万)":  round(np_ / 1e6, 0)   if np_   > 0 else None,
            "営業CF(百万)":  round(cfo / 1e6, 0)   if cfo   > 0 else None,
        }
    except Exception as e:
        return {"error": str(e)}

# ========================================================
# ===== サイドバー =====
# ========================================================

with st.sidebar:
    # ---- データ管理 ----
    st.markdown("### 🗂️ データ管理")

    csv_files = get_csv_files()
    if not csv_files:
        st.error("CSVファイルが見つかりません")
        st.stop()

    csv_labels = [os.path.basename(f) for f in csv_files]
    sel_label  = st.selectbox("📂 データファイル", csv_labels, index=0)
    csv_path   = csv_files[csv_labels.index(sel_label)]

    if st.button("🚀 最新データ取得", use_container_width=True, type="primary"):
        with st.spinner("データ取得中..."):
            try:
                r = subprocess.run(
                    [VENV_PYTHON, os.path.join(DATA_DIR, "fetch_3months.py")],
                    capture_output=True, text=True, timeout=300,
                )
                if r.returncode == 0:
                    st.success("✅ 取得完了！")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(r.stderr[:400])
            except Exception as e:
                st.error(str(e))

    st.divider()

    # ---- テクニカル指標 ----
    st.markdown("### 📊 テクニカル指標")
    ind_ma5   = st.checkbox("📈 移動平均 MA5",   value=True)
    ind_ma25  = st.checkbox("📈 移動平均 MA25",  value=True)
    ind_ma75  = st.checkbox("📈 移動平均 MA75",  value=False)
    ind_bb    = st.checkbox("📉 ボリンジャーバンド", value=False)
    ind_rsi   = st.checkbox("🔵 RSI",            value=True)
    ind_macd  = st.checkbox("🟡 MACD",           value=True)
    ind_stoch = st.checkbox("🔴 ストキャスティクス", value=False)
    ind_vol   = st.checkbox("📊 出来高",          value=True)

    indicators = (
        (["MA5"]   if ind_ma5   else []) +
        (["MA25"]  if ind_ma25  else []) +
        (["MA75"]  if ind_ma75  else []) +
        (["BB"]    if ind_bb    else []) +
        (["RSI"]   if ind_rsi   else []) +
        (["MACD"]  if ind_macd  else []) +
        (["STOCH"] if ind_stoch else [])
    )

    st.divider()

    # ---- バックテスト設定 ----
    st.markdown("### 🔬 バックテスト設定")
    capital      = st.number_input("初期資金(円)", value=1_000_000, step=100_000)
    take_profit  = st.slider("利確(%)",  1, 50, 10) / 100
    stop_loss    = st.slider("損切(%)",  1, 30,  5) / 100
    entry_ma     = st.checkbox("MAクロス エントリー",   value=True)
    entry_rsi_bt = st.checkbox("RSI売られすぎ エントリー", value=False)
    entry_macd_bt= st.checkbox("MACDクロス エントリー", value=False)
    exit_ma      = st.checkbox("MAクロス エグジット",    value=True)
    rsi_entry_th = st.slider("RSIエントリー閾値", 10, 50, 30)

# ========================================================
# ===== メインエリア =====
# ========================================================

# データ読み込み
df = load_csv(csv_path)

# ヘッダー情報
st.markdown("""
<h1 style='margin-bottom:0'>
🔍 株スクリーニング ＋ 📊 バックテスト ＋ 💹 ファンダ分析
</h1>
""", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("📁 ファイル", sel_label[:20] + "…")
m2.metric("📈 銘柄数",   f"{df['Code'].nunique():,} 銘柄")
m3.metric("📅 期間",     f"{df['Date'].min().date()} …")
m4.metric("📋 レコード数", f"{len(df):,} 件")

st.divider()

# ========================================================
# ===== STEP 1: スクリーニング =====
# ========================================================

st.markdown('<div class="step-header"><h3>🔍 STEP 1 ─ スクリーニング条件</h3></div>',
            unsafe_allow_html=True)

with st.expander("▼ 条件を設定", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        vol_min    = st.number_input("最小出来高",          value=100_000, step=10_000)
        mktcap_min = st.number_input("最小時価総額(百万円)", value=1_000,   step=100)
    with c2:
        ma5_over_ma25  = st.checkbox("MA5 > MA25",  value=True)
        ma25_over_ma75 = st.checkbox("MA25 > MA75", value=False)
    with c3:
        rsi_lo = st.number_input("RSI下限", value=0,   min_value=0,   max_value=100)
        rsi_hi = st.number_input("RSI上限", value=100, min_value=0,   max_value=100)

c_btn, c_num = st.columns([3, 1])
with c_btn:
    do_screen = st.button("🔍 スクリーニング実行",
                          type="primary", use_container_width=True)
with c_num:
    max_results = st.number_input("最大表示件数", value=50, min_value=5,
                                  max_value=500, step=5)

# セッション初期化
if "scr_result" not in st.session_state:
    st.session_state.scr_result = None
if "selected_codes" not in st.session_state:
    st.session_state.selected_codes = []

if do_screen:
    params = {
        "vol_min":        vol_min,
        "mktcap_min":     mktcap_min * 1e6,
        "ma5_above_ma25": ma5_over_ma25,
        "ma25_above_ma75":ma25_over_ma75,
        "rsi_min":        rsi_lo if rsi_lo > 0   else None,
        "rsi_max":        rsi_hi if rsi_hi < 100 else None,
    }
    with st.spinner("スクリーニング中..."):
        result = run_screening(df, params)
        st.session_state.scr_result = result.head(max_results)
        st.session_state.selected_codes = []

# ========================================================
# ===== STEP 2: 銘柄選択 =====
# ========================================================

if st.session_state.scr_result is not None:
    scr_df = st.session_state.scr_result

    st.markdown('<div class="step-header"><h3>✅ STEP 2 ─ 銘柄選択</h3></div>',
                unsafe_allow_html=True)
    st.success(f"✅ {len(scr_df)} 銘柄が条件に一致しました")

    # 全選択 / 全解除
    col_a, col_b, _ = st.columns([1, 1, 6])
    if col_a.button("☑ 全選択"):
        st.session_state.selected_codes = scr_df["Code"].tolist()
    if col_b.button("□ 全解除"):
        st.session_state.selected_codes = []

    # データエディタで選択
    scr_display = scr_df.copy()
    scr_display.insert(0, "選択", scr_display["Code"].isin(
        st.session_state.selected_codes))

    edited = st.data_editor(
        scr_display,
        column_config={
            "選択": st.column_config.CheckboxColumn("選択", default=False),
            "Close": st.column_config.NumberColumn("株価(円)", format="¥%.1f"),
            "前日比(%)": st.column_config.NumberColumn("前日比(%)", format="%.2f%%"),
            "MktCap(百万)": st.column_config.NumberColumn("時価総額(百万)", format="%.0f"),
        },
        use_container_width=True,
        hide_index=True,
        key="stock_selector",
    )
    st.session_state.selected_codes = edited[edited["選択"] == True]["Code"].tolist()
    selected = st.session_state.selected_codes

    if not selected:
        st.info("👆 チェックボックスで分析する銘柄を選択してください")
    else:
        st.success(f"📌 選択中: {len(selected)} 銘柄　─　{', '.join(selected)}")

        # ========================================================
        # ===== STEP 3 〜 6 (選択銘柄ごと) =====
        # ========================================================

        do_bt = st.button("▶️ バックテスト実行", type="primary",
                          use_container_width=True)

        for code in selected:
            code_row = scr_df[scr_df["Code"] == code]
            name = code_row["Name"].values[0] if not code_row.empty else code
            sdf_all = df[df["Code"] == code].sort_values("Date")

            st.markdown("---")
            st.markdown(f"## 📌 {code}　{name}")

            # ---- タブで整理 ----
            tab_chart, tab_bt, tab_funda = st.tabs(
                ["📈 チャート", "🔬 バックテスト", "💹 ファンダメンタル"])

            # ===== チャートタブ =====
            with tab_chart:
                col_period, _ = st.columns([2, 6])
                with col_period:
                    period_sel = st.selectbox(
                        "表示期間",
                        ["1ヶ月", "3ヶ月", "6ヶ月", "1年", "全期間"],
                        index=2,
                        key=f"period_{code}",
                    )
                pm = {"1ヶ月": 21, "3ヶ月": 63, "6ヶ月": 126,
                      "1年": 252, "全期間": len(sdf_all)}
                sdf = sdf_all.tail(pm[period_sel])
                st.plotly_chart(
                    create_chart(sdf, code, name, indicators, show_vol=ind_vol),
                    use_container_width=True,
                )

            # ===== バックテストタブ =====
            with tab_bt:
                if do_bt:
                    sp = {
                        "capital":      capital,
                        "take_profit":  take_profit,
                        "stop_loss":    stop_loss,
                        "entry_ma":     entry_ma,
                        "entry_rsi":    entry_rsi_bt,
                        "entry_macd":   entry_macd_bt,
                        "exit_ma":      exit_ma,
                        "rsi_entry":    rsi_entry_th,
                    }
                    trades_df, summary, _ = run_backtest(df, code, sp)

                    if summary:
                        # サマリーメトリクス
                        keys   = list(summary.keys())
                        vals   = list(summary.values())
                        n_cols = 4
                        for row_i in range(0, len(keys), n_cols):
                            cols = st.columns(n_cols)
                            for ci, (k, v) in enumerate(
                                    zip(keys[row_i:row_i+n_cols],
                                        vals[row_i:row_i+n_cols])):
                                delta_color = "normal"
                                if "損益" in k or "リターン" in k:
                                    delta_color = "inverse" if v < 0 else "normal"
                                cols[ci].metric(k, f"{v:,.1f}" if isinstance(v, float)
                                                else f"{v:,}")

                        # トレード一覧
                        if trades_df is not None and not trades_df.empty:
                            with st.expander("📋 トレード一覧", expanded=False):
                                st.dataframe(trades_df, use_container_width=True)

                            # 損益グラフ
                            colors = ["#ef4444" if p > 0 else "#3b82f6"
                                      for p in trades_df["損益(円)"]]
                            fig_pnl = go.Figure(go.Bar(
                                x=trades_df["エグジット日"].astype(str),
                                y=trades_df["損益(円)"],
                                marker_color=colors,
                                text=trades_df["リターン(%)"].apply(
                                    lambda x: f"{x:+.1f}%"),
                                textposition="outside",
                            ))
                            fig_pnl.update_layout(
                                title="📊 トレード損益",
                                template="plotly_dark",
                                height=350,
                                margin=dict(t=50, b=30),
                            )
                            st.plotly_chart(fig_pnl, use_container_width=True)

                            # 累積損益グラフ
                            cum_pnl = trades_df["損益(円)"].cumsum()
                            fig_cum = go.Figure(go.Scatter(
                                x=trades_df["エグジット日"].astype(str),
                                y=cum_pnl,
                                mode="lines+markers",
                                line=dict(color="#a78bfa", width=2),
                                fill="tozeroy",
                                fillcolor="rgba(167,139,250,0.15)",
                            ))
                            fig_cum.update_layout(
                                title="📈 累積損益",
                                template="plotly_dark",
                                height=300,
                                margin=dict(t=50, b=30),
                            )
                            st.plotly_chart(fig_cum, use_container_width=True)
                        else:
                            st.warning("⚠️ トレードが発生しませんでした")
                    else:
                        st.warning("⚠️ バックテスト結果なし（データ不足）")
                else:
                    st.info("👈 サイドバーの設定を確認後、「▶️ バックテスト実行」を押してください")

            # ===== ファンダメンタルタブ =====
            with tab_funda:
                cur_price = float(sdf_all["AdjC"].iloc[-1]) if not sdf_all.empty else 0
                with st.spinner(f"{code} のファンダメンタルデータ取得中..."):
                    funda = fetch_fundamental(code, cur_price)

                if funda is None:
                    st.info("ℹ️ ファンダメンタルデータが見つかりませんでした")
                elif "error" in funda:
                    st.warning(f"⚠️ エラー: {funda['error']}")
                else:
                    # 主要指標
                    st.markdown("#### 📊 主要バリュエーション指標")
                    key_metrics = ["PER(倍)", "PBR(倍)", "ROE(%)",
                                   "配当利回り(%)", "EPS(円)", "BPS(円)"]
                    cols_f = st.columns(len(key_metrics))
                    for ci, km in enumerate(key_metrics):
                        v = funda.get(km)
                        cols_f[ci].metric(km, f"{v}" if v is not None else "N/A")

                    st.markdown("#### 📋 業績データ")
                    perf_metrics = {k: v for k, v in funda.items()
                                    if k not in key_metrics}
                    cols_p = st.columns(4)
                    for ci, (k, v) in enumerate(perf_metrics.items()):
                        cols_p[ci % 4].metric(
                            k, f"{v:,.0f}" if isinstance(v, float) and v is not None
                            else str(v) if v is not None else "N/A")

                    # レーダーチャート
                    radar_keys  = ["PER(倍)", "PBR(倍)", "ROE(%)", "配当利回り(%)"]
                    radar_vals  = [funda.get(k) or 0 for k in radar_keys]
                    if any(v > 0 for v in radar_vals):
                        fig_radar = go.Figure(go.Scatterpolar(
                            r=radar_vals,
                            theta=radar_keys,
                            fill="toself",
                            fillcolor="rgba(124,58,237,0.2)",
                            line=dict(color="#7c3aed"),
                        ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True)),
                            template="plotly_dark",
                            height=350,
                            title="バリュエーション レーダー",
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)