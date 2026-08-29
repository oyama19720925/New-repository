<<<<<<< HEAD
import glob
import os
import subprocess
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# API設定（Streamlit secretsを優先、なければ環境変数またはデフォルト値）
try:
    API_KEY = st.secrets.get("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
except Exception:
    API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
API_BASE = "https://api.jquants.com/v2"
VENV_PYTHON = r"C:\stock_system\venv\Scripts\python.exe"
DATA_DIR = r"C:\stock_system"

st.set_page_config(page_title="株式分析システム", layout="wide")


@st.cache_data
def get_csv_files():
    files = glob.glob(os.path.join(DATA_DIR, "stocks_OHLC_*.csv"))
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def load_csv(filepath):
    df = pd.read_csv(filepath, dtype={"Code": str})
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def calc_ma(df, period):
    return df["AdjC"].rolling(period).mean()


def calc_rsi(df, period=14):
    delta = df["AdjC"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df["AdjC"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["AdjC"].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist


def calc_bollinger(df, period=20, std=2):
    ma = df["AdjC"].rolling(period).mean()
    sigma = df["AdjC"].rolling(period).std()
    upper = ma + std * sigma
    lower = ma - std * sigma
    return upper, ma, lower


def screening(df, params):
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
        ma5 = calc_ma(stock_df, 5).iloc[-1]
        ma25 = calc_ma(stock_df, 25).iloc[-1]
        ma75 = calc_ma(stock_df, 75).iloc[-1] if len(stock_df) >= 75 else None

        if params.get("ma5_above_ma25") and not (ma5 > ma25):
            continue
        if params.get("ma25_above_ma75") and ma75 is not None and not (ma25 > ma75):
            continue

        rsi = calc_rsi(stock_df).iloc[-1]
        if params.get("rsi_min") and not np.isnan(rsi) and rsi < params["rsi_min"]:
            continue
        if params.get("rsi_max") and not np.isnan(rsi) and rsi > params["rsi_max"]:
            continue

        results.append({
            "Code": code,
            "Name": row.get("Name", ""),
            "Sector": row.get("Sector", ""),
            "Close": round(row["AdjC"], 1),
            "Volume": int(row["AdjVo"]),
            "MktCap": row.get("MktCap", 0),
            "MA5": round(ma5, 1),
            "MA25": round(ma25, 1),
            "RSI": round(rsi, 1) if not np.isnan(rsi) else None,
        })
    return pd.DataFrame(results)


def backtest(df, code, strategy_params):
    stock_df = df[df["Code"] == code].sort_values("Date").copy().reset_index(drop=True)
    if len(stock_df) < 30:
        return None, None, None

    stock_df["MA5"] = calc_ma(stock_df, 5)
    stock_df["MA25"] = calc_ma(stock_df, 25)
    stock_df["RSI"] = calc_rsi(stock_df)
    macd, sig, _ = calc_macd(stock_df)
    stock_df["MACD"] = macd
    stock_df["Signal"] = sig

    trades = []
    position = None
    capital = strategy_params.get("capital", 1000000)
    initial_capital = capital

    for i in range(26, len(stock_df)):
        row = stock_df.iloc[i]
        prev = stock_df.iloc[i - 1]
        buy_signal = False
        sell_signal = False

        if strategy_params.get("entry_ma"):
            if prev["MA5"] <= prev["MA25"] and row["MA5"] > row["MA25"]:
                buy_signal = True
        if strategy_params.get("entry_rsi"):
            if not np.isnan(row["RSI"]) and row["RSI"] < strategy_params.get("rsi_entry", 30):
                buy_signal = True
        if strategy_params.get("entry_macd"):
            if prev["MACD"] <= prev["Signal"] and row["MACD"] > row["Signal"]:
                buy_signal = True

        if position:
            chg = (row["AdjC"] - position["entry_price"]) / position["entry_price"]
            if chg >= strategy_params.get("take_profit", 0.1):
                sell_signal = True
            if chg <= -strategy_params.get("stop_loss", 0.05):
                sell_signal = True
            if strategy_params.get("exit_ma"):
                if prev["MA5"] >= prev["MA25"] and row["MA5"] < row["MA25"]:
                    sell_signal = True

        if buy_signal and not position:
            shares = int(capital // row["AdjC"])
            if shares > 0:
                position = {"entry_date": row["Date"], "entry_price": row["AdjC"], "shares": shares}
                capital -= shares * row["AdjC"]
        elif sell_signal and position:
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
        summary["総トレード数"] = len(trades_df)
        summary["勝率(%)"] = round(len(trades_df[trades_df["損益(円)"] > 0]) / len(trades_df) * 100, 1)
        summary["総損益(円)"] = round(trades_df["損益(円)"].sum(), 0)
        summary["平均損益(円)"] = round(trades_df["損益(円)"].mean(), 0)
        summary["最大利益(円)"] = round(trades_df["損益(円)"].max(), 0)
        summary["最大損失(円)"] = round(trades_df["損益(円)"].min(), 0)
        final = capital + (position["shares"] * stock_df.iloc[-1]["AdjC"] if position else 0)
        summary["最終資本(円)"] = round(final, 0)
        summary["総リターン(%)"] = round((final - initial_capital) / initial_capital * 100, 2)

    return trades_df, summary, stock_df


def create_chart(stock_df, code, name, indicators):
    rows = 1
    row_heights = [0.6]
    if "RSI" in indicators:
        rows += 1
        row_heights.append(0.2)
    if "MACD" in indicators:
        rows += 1
        row_heights.append(0.2)

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
    )
    fig.add_trace(
        go.Candlestick(
            x=stock_df["Date"],
            open=stock_df["AdjO"],
            high=stock_df["AdjH"],
            low=stock_df["AdjL"],
            close=stock_df["AdjC"],
            name="価格",
            increasing_line_color="red",
            decreasing_line_color="blue",
        ),
        row=1,
        col=1,
    )
    if "MA5" in indicators:
        fig.add_trace(
            go.Scatter(x=stock_df["Date"], y=calc_ma(stock_df, 5), name="MA5", line=dict(color="orange", width=1)),
            row=1,
            col=1,
        )
    if "MA25" in indicators:
        fig.add_trace(
            go.Scatter(x=stock_df["Date"], y=calc_ma(stock_df, 25), name="MA25", line=dict(color="cyan", width=1)),
            row=1,
            col=1,
        )
    if "MA75" in indicators:
        fig.add_trace(
            go.Scatter(x=stock_df["Date"], y=calc_ma(stock_df, 75), name="MA75", line=dict(color="lime", width=1)),
            row=1,
            col=1,
        )
    if "BB" in indicators:
        upper, _, lower = calc_bollinger(stock_df)
        fig.add_trace(
            go.Scatter(x=stock_df["Date"], y=upper, name="BB上", line=dict(color="gray", dash="dash", width=1)),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=stock_df["Date"],
                y=lower,
                name="BB下",
                line=dict(color="gray", dash="dash", width=1),
                fill="tonexty",
                fillcolor="rgba(128,128,128,0.1)",
            ),
            row=1,
            col=1,
        )

    cur_row = 2
    if "RSI" in indicators:
        rsi = calc_rsi(stock_df)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=rsi, name="RSI", line=dict(color="purple", width=1)), row=cur_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=cur_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=cur_row, col=1)
        cur_row += 1

    if "MACD" in indicators:
        macd, sig, hist = calc_macd(stock_df)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=macd, name="MACD", line=dict(color="blue", width=1)), row=cur_row, col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=sig, name="Signal", line=dict(color="red", width=1)), row=cur_row, col=1)
        bar_colors = ["red" if v >= 0 else "blue" for v in hist]
        fig.add_trace(go.Bar(x=stock_df["Date"], y=hist, name="Hist", marker_color=bar_colors), row=cur_row, col=1)

    fig.update_layout(
        title=f"{code}  {name}",
        height=600 + 150 * (rows - 1),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
    )
    return fig


def fetch_fundamental(code, current_price):
    headers = {"X-API-KEY": API_KEY}
    url = f"{API_BASE}/fins/summary"
    try:
        resp = requests.get(url, headers=headers, params={"code": code}, timeout=10)
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
            except (ValueError, TypeError):
                return 0.0

        eps = f("EPS")
        bps = f("BPS")
        roe = f("ROE")
        sales = f("Sales")
        op = f("OP")
        np_ = f("NP")
        cfo = f("CFO")
        feps = f("FEPS")
        fdiv = f("FDivAnn")

        per = round(current_price / eps, 1) if eps > 0 else None
        pbr = round(current_price / bps, 2) if bps > 0 else None
        div_yield = round(fdiv / current_price * 100, 2) if fdiv > 0 and current_price > 0 else None
        roe_pct = round(roe * 100, 1) if 0 < roe < 1 else round(roe, 1) if roe != 0 else None

        return {
            "PER": per,
            "PBR": pbr,
            "ROE(%)": roe_pct,
            "EPS(円)": round(eps, 1),
            "BPS(円)": round(bps, 1),
            "配当利回り(%)": div_yield,
            "年間配当(円)": fdiv,
            "予想EPS(円)": round(feps, 1),
            "売上高(百万)": round(sales / 1e6, 0) if sales > 0 else None,
            "営業利益(百万)": round(op / 1e6, 0) if op > 0 else None,
            "純利益(百万)": round(np_ / 1e6, 0) if np_ > 0 else None,
            "営業CF(百万)": round(cfo / 1e6, 0) if cfo > 0 else None,
        }
    except Exception as e:
        return {"error": str(e)}


# ===== UI =====
st.title("📈 株式分析システム")

with st.sidebar:
    st.header("⚙️ データ管理")
    csv_files = get_csv_files()
    if not csv_files:
        st.error("CSVファイルが見つかりません")
        st.stop()
    csv_labels = [os.path.basename(f) for f in csv_files]
    selected_label = st.selectbox("📂 データファイル", csv_labels, index=0)
    csv_path = csv_files[csv_labels.index(selected_label)]

    if st.button("🔄 データ更新"):
        with st.spinner("取得中..."):
            try:
                r = subprocess.run([VENV_PYTHON, os.path.join(DATA_DIR, "fetch_3months.py")], capture_output=True, text=True, timeout=300)
                if r.returncode == 0:
                    st.success("✅ 完了")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(r.stderr[:300])
            except Exception as e:
                st.error(str(e))
    st.divider()
    st.header("📊 テクニカル指標")
    ind_ma5 = st.checkbox("MA5", value=True)
    ind_ma25 = st.checkbox("MA25", value=True)
    ind_ma75 = st.checkbox("MA75", value=False)
    ind_bb = st.checkbox("ボリンジャーバンド", value=False)
    ind_rsi = st.checkbox("RSI", value=True)
    ind_macd = st.checkbox("MACD", value=True)
    indicators = (
        (["MA5"] if ind_ma5 else [])
        + (["MA25"] if ind_ma25 else [])
        + (["MA75"] if ind_ma75 else [])
        + (["BB"] if ind_bb else [])
        + (["RSI"] if ind_rsi else [])
        + (["MACD"] if ind_macd else [])
    )


@st.cache_data
def load_data(path):
    return load_csv(path)


df = load_data(csv_path)
st.info(f"📅 {df['Date'].min().date()} ～ {df['Date'].max().date()}  |  銘柄数: {df['Code'].nunique()}")

# ---- STEP 1: スクリーニング ----
st.header("🔍 STEP 1: スクリーニング")
with st.expander("スクリーニング条件を設定", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        vol_min = st.number_input("最小出来高", value=100000, step=10000)
        mktcap_min = st.number_input("最小時価総額(百万円)", value=1000, step=100)
    with c2:
        ma5_over_ma25 = st.checkbox("MA5 > MA25", value=True)
        ma25_over_ma75 = st.checkbox("MA25 > MA75", value=False)
    with c3:
        rsi_lo = st.number_input("RSI下限", value=0, min_value=0, max_value=100)
        rsi_hi = st.number_input("RSI上限", value=100, min_value=0, max_value=100)
    do_screen = st.button("🔍 スクリーニング実行", type="primary")

if "scr_result" not in st.session_state:
    st.session_state.scr_result = None

if do_screen:
    params = {
        "vol_min": vol_min,
        "mktcap_min": mktcap_min * 1e6,
        "ma5_above_ma25": ma5_over_ma25,
        "ma25_above_ma75": ma25_over_ma75,
        "rsi_min": rsi_lo if rsi_lo > 0 else None,
        "rsi_max": rsi_hi if rsi_hi < 100 else None,
    }
    with st.spinner("スクリーニング中..."):
        st.session_state.scr_result = screening(df, params)

if st.session_state.scr_result is not None:
    scr_df = st.session_state.scr_result
    st.success(f"✅ {len(scr_df)} 銘柄ヒット")

    # ---- STEP 2: 銘柄選択 ----
    st.header("✅ STEP 2: 分析する銘柄を選択")
    if scr_df.empty:
        st.warning("条件に一致する銘柄がありませんでした。条件を緩めてください。")
    else:
        st.dataframe(scr_df, use_container_width=True, hide_index=True)

        options = [f"{row['Code']} - {row['Name']}" for _, row in scr_df.iterrows()]
        selected_labels = st.multiselect("分析対象銘柄を選択してください", options=options, default=options[:1] if options else [])
        selected = [label.split(" - ")[0] for label in selected_labels]

        if not selected:
            st.info("👆 リストから銘柄を選択してください")
        else:
            # ---- STEP 3: チャート ----
            st.header("📈 STEP 3: チャート")
            for code in selected:
                sdf = df[df["Code"] == code].sort_values("Date")
                name_series = scr_df[scr_df["Code"] == code]["Name"].values
                name = name_series[0] if len(name_series) > 0 else ""
                col_l, col_r = st.columns([4, 1])
                with col_r:
                    period_sel = st.selectbox("表示期間", ["3ヶ月", "6ヶ月", "1年", "全期間"], key=f"p_{code}")
                pm = {"3ヶ月": 63, "6ヶ月": 126, "1年": 252, "全期間": len(sdf)}
                sdf = sdf.tail(pm[period_sel])
                st.plotly_chart(create_chart(sdf, code, name, indicators), use_container_width=True)

            # ---- STEP 4: バックテスト設定 ----
            st.header("🔬 STEP 4: バックテスト")
            with st.expander("バックテスト設定", expanded=True):
                b1, b2, b3 = st.columns(3)
                with b1:
                    capital = st.number_input("初期資金(円)", value=1000000, step=100000)
                    take_profit = st.slider("利確(%)", 1, 50, 10) / 100
                    stop_loss = st.slider("損切(%)", 1, 30, 5) / 100
                with b2:
                    entry_ma = st.checkbox("MAクロス エントリー", value=True)
                    entry_rsi = st.checkbox("RSI売られすぎ エントリー", value=False)
                    entry_macd = st.checkbox("MACDクロス エントリー", value=False)
                with b3:
                    exit_ma = st.checkbox("MAクロス エグジット", value=True)
                    rsi_entry_th = st.slider("RSIエントリー閾値", 10, 50, 30)
                do_bt = st.button("▶️ バックテスト実行", type="primary")

            if do_bt:
                sp = {
                    "capital": capital,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "entry_ma": entry_ma,
                    "entry_rsi": entry_rsi,
                    "entry_macd": entry_macd,
                    "exit_ma": exit_ma,
                    "rsi_entry": rsi_entry_th,
                }
                for code in selected:
                    name_series = scr_df[scr_df["Code"] == code]["Name"].values
                    name = name_series[0] if len(name_series) > 0 else ""
                    st.subheader(f"📊 {code}  {name}")

                    trades_df, summary, _ = backtest(df, code, sp)

                    # ---- STEP 5: バックテスト結果 ----
                    st.markdown("#### 📋 STEP 5: バックテスト結果")
                    if summary:
                        cols = st.columns(4)
                        for i, (k, v) in enumerate(summary.items()):
                            cols[i % 4].metric(k, v)
                        if trades_df is not None and not trades_df.empty:
                            st.dataframe(trades_df, use_container_width=True)
                            fig_pnl = go.Figure(
                                go.Bar(
                                    x=trades_df["エグジット日"].astype(str),
                                    y=trades_df["損益(円)"],
                                    marker_color=["red" if p > 0 else "steelblue" for p in trades_df["損益(円)"]],
                                )
                            )
                            fig_pnl.update_layout(title="トレード損益", template="plotly_dark", height=300)
                            st.plotly_chart(fig_pnl, use_container_width=True)
                    else:
                        st.warning("トレードが発生しませんでした")

                    # ---- STEP 6: ファンダメンタル ----
                    st.markdown("#### 💹 STEP 6: ファンダメンタル分析")
                    cur_price = float(df[df["Code"] == code]["AdjC"].iloc[-1])
                    with st.spinner("取得中..."):
                        funda = fetch_fundamental(code, cur_price)
                    if funda is None:
                        st.info("データなし")
                    elif "error" in funda:
                        st.warning(f"エラー: {funda['error']}")
                    else:
                        fc = st.columns(4)
                        for i, (k, v) in enumerate(funda.items()):
                            fc[i % 4].metric(k, v if v is not None else "N/A")
                    st.divider()
=======
import os
import sys
import glob
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st

# ===== 設定 =====
try:
    API_KEY = st.secrets.get("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
except Exception:
    API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")

API_BASE = "https://api.jquants.com/v2"
CURRENT_PYTHON = sys.executable
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="株式スクリーニング＆分析システム", layout="wide", page_icon="📈")

# ===== CSS =====
st.markdown("""
<style>
.step-header {
    background: linear-gradient(90deg, #7c3aed22, transparent);
    border-left: 4px solid #7c3aed;
    padding: 8px 16px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0 12px 0;
}
.metric-box {
    background: #1e1e2e;
    border-radius: 8px;
    padding: 10px 14px;
    border: 1px solid #313244;
    margin-bottom: 8px;
}
.positive { color: #ef4444; }
.negative { color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

def get_csv_files():
    # ルート階層および data/ フォルダの両方を自動探索
    patterns = [
        os.path.join(DATA_DIR, "stocks_*.csv"),
        os.path.join(DATA_DIR, "data", "stocks_*.csv"),
        os.path.join(DATA_DIR, "*.csv"),
        os.path.join(DATA_DIR, "data", "*.csv"),
        "stocks_*.csv",
        "*.csv"
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    files = list(set(files))
    # requirements.txt など CSV 以外が混入しないよう除外
    files = [f for f in files if f.endswith(".csv")]
    files.sort(key=os.path.getmtime, reverse=True)
    return files

@st.cache_data
def load_csv(filepath):
    df = pd.read_csv(filepath, dtype={"Code": str})
    df["Date"] = pd.to_datetime(df["Date"])
    df["Code"] = df["Code"].astype(str).str.strip()

    for num_col in ["AdjVo", "Volume", "AdjC", "AdjO", "AdjH", "AdjL", "MktCap", "BPS", "EPS", "FEPS", "NxFEPS"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    return df

def calc_ma(series, period):
    return series.rolling(period).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist

def calc_bollinger(series, period=20, std_mult=2):
    ma = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    return ma + std_mult * sigma, ma, ma - std_mult * sigma

def calc_stoch(df, k=14, d=3, sd=3):
    low_min = df["AdjL"].rolling(k).min()
    high_max = df["AdjH"].rolling(k).max()
    fast_k = 100 * ((df["AdjC"] - low_min) / (high_max - low_min).replace(0, np.nan))
    slow_k = fast_k.rolling(d).mean()
    slow_d = slow_k.rolling(sd).mean()
    return slow_k, slow_d

# ===== J-Quants V2 ファンダメンタルズ詳細取得 =====
@st.cache_data(ttl=3600)
def fetch_fundamental_v2(code, current_price):
    headers = {"x-api-key": API_KEY}
    url = f"{API_BASE}/fins/summary"
    c_str = str(code).strip()
    c4 = c_str[:4]
    c5 = f"{c4}0" if len(c4) == 4 else c_str

    items = []
    for c in [c5, c4]:
        try:
            resp = requests.get(url, headers=headers, params={"code": c}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                summary_list = data.get("fins_summary") or data.get("data") or data.get("summary") or []
                if summary_list:
                    items = summary_list
                    break
        except Exception:
            continue

    if not items:
        return None

    items_sorted = sorted(items, key=lambda x: str(x.get("DisclosedDate") or x.get("DiscDate") or x.get("CurPeriodEndDate") or ""))
    latest_rec = items_sorted[-1]

    def to_f(v):
        if v not in (None, "", "None", "-", "－", "null"):
            try:
                return float(v)
            except (ValueError, TypeError):
                return 0.0
        return 0.0

    eps = to_f(latest_rec.get("EarningsPerShare") or latest_rec.get("EPS") or latest_rec.get("NetIncomePerShare"))
    bps = to_f(latest_rec.get("BookValuePerShare") or latest_rec.get("BPS") or latest_rec.get("NetAssetsPerShare"))
    roe = to_f(latest_rec.get("ReturnOnEquity") or latest_rec.get("ROE"))
    sales = to_f(latest_rec.get("NetSales") or latest_rec.get("Sales") or latest_rec.get("OperatingRevenue"))
    op = to_f(latest_rec.get("OperatingProfit") or latest_rec.get("OP") or latest_rec.get("OperatingIncome"))
    np_ = to_f(latest_rec.get("ProfitLossAttributableToOwnersOfParent") or latest_rec.get("NP") or latest_rec.get("NetIncome"))

    feps = to_f(latest_rec.get("ForecastEarningsPerShareAnnual") or latest_rec.get("ForecastEarningsPerShare") or latest_rec.get("FEPS"))
    nxfeps = to_f(latest_rec.get("NextForecastEarningsPerShareAnnual") or latest_rec.get("NextForecastEarningsPerShare") or latest_rec.get("NxFEPS"))
    fdiv = to_f(latest_rec.get("ForecastDividendPerShareAnnual") or latest_rec.get("FDivAnn") or latest_rec.get("DividendPerShareAnnual"))

    if eps == 0.0 or bps == 0.0:
        for rec in reversed(items_sorted[:-1]):
            if eps == 0.0:
                eps = to_f(rec.get("EarningsPerShare") or rec.get("EPS") or rec.get("NetIncomePerShare"))
            if bps == 0.0:
                bps = to_f(rec.get("BookValuePerShare") or rec.get("BPS") or rec.get("NetAssetsPerShare"))

    per = round(current_price / eps, 1) if eps > 0 else None
    next_per = round(current_price / feps, 1) if feps > 0 else None
    nx_per = round(current_price / nxfeps, 1) if nxfeps > 0 else None
    pbr = round(current_price / bps, 2) if bps > 0 else None
    div_yield = round(fdiv / current_price * 100, 2) if fdiv > 0 and current_price > 0 else None
    roe_pct = round(roe * 100, 1) if 0 < roe < 1 else round(roe, 1) if roe != 0 else None

    eps_growth = None
    if feps > 0 and nxfeps > 0:
        eps_growth = round(((nxfeps / feps) - 1.0) * 100.0, 2)

    return {
        "PER(倍)": per, "来期PER(倍)": next_per, "さ来期PER(倍)": nx_per, "PBR(倍)": pbr, "ROE(%)": roe_pct,
        "EPS(円)": round(eps, 1) if eps else None, "BPS(円)": round(bps, 1) if bps else None,
        "来期予想EPS(円)": round(feps, 1) if feps else None, "さ来期予想EPS(円)": round(nxfeps, 1) if nxfeps else None,
        "さ来期EPS成長率(%)": eps_growth,
        "配当利回り(%)": div_yield, "年間配当(円)": fdiv if fdiv else None,
        "売上高(百万)": round(sales / 1e6, 0) if sales > 0 else None,
        "営業利益(百万)": round(op / 1e6, 0) if op > 0 else None,
        "純利益(百万)": round(np_ / 1e6, 0) if np_ > 0 else None,
    }

# ===== PBR・EPS成長率対応スクリーニング =====
def run_screening(df, params):
    columns = [
        "Code", "Name", "Market", "Sector", "Close", "前日比(%)", "PBR", "来期予想EPS", "さ来期予想EPS", "さ来期EPS成長率(%)",
        "来期PER", "さ来期PER", "Volume", "MktCap(百万)", "MA_Short", "MA_Long", "MACD", "Signal", "RSI", "Stoch_%K", "Stoch_%D"
    ]

    target_markets = params.get("target_markets", ["東証全部"])
    use_vol = params.get("use_vol", False)
    vol_min = params.get("vol_min", 0)
    use_mktcap = params.get("use_mktcap", False)
    mktcap_min = params.get("mktcap_min", 0)
    vol_col = "AdjVo" if "AdjVo" in df.columns else "Volume"

    use_pbr = params.get("use_pbr", False)
    pbr_max = params.get("pbr_max", 1.5)

    use_eps_growth = params.get("use_eps_growth", False)
    eps_growth_min = params.get("eps_growth_min", 0.0)
    eps_growth_max = params.get("eps_growth_max", 1000.0)

    use_ma_cross = params.get("use_ma_cross", False)
    use_macd_cross = params.get("use_macd_cross", False)
    use_rsi = params.get("use_rsi", False)
    use_stoch = params.get("use_stoch", False)

    results = []
    grouped = df.groupby("Code")

    for code, stock_df in grouped:
        stock_df = stock_df.sort_values("Date")
        if len(stock_df) < 2:
            continue

        row = stock_df.iloc[-1]
        market = str(row.get("Market", "その他"))

        if "東証全部" not in target_markets and len(target_markets) > 0:
            if market not in target_markets:
                continue

        raw_vol = row.get(vol_col, 0)
        safe_volume = int(raw_vol) if pd.notnull(raw_vol) and not np.isnan(raw_vol) else 0
        if use_vol and safe_volume < vol_min:
            continue

        mkt_cap = row.get("MktCap", 0)
        if use_mktcap and (pd.isna(mkt_cap) or mkt_cap < mktcap_min):
            continue

        price = float(row["AdjC"])
        adj = stock_df["AdjC"]

        bps = row.get("BPS")
        feps = row.get("FEPS")
        nxfeps = row.get("NxFEPS")

        pbr_val = round(price / bps, 2) if pd.notnull(bps) and bps > 0 else None
        next_per = round(price / feps, 1) if pd.notnull(feps) and feps > 0 else None
        nx_per = round(price / nxfeps, 1) if pd.notnull(nxfeps) and nxfeps > 0 else None

        eps_growth = None
        if pd.notnull(feps) and pd.notnull(nxfeps) and feps > 0:
            eps_growth = round(((nxfeps / feps) - 1.0) * 100.0, 2)

        if use_pbr:
            if pbr_val is None or pbr_val > pbr_max:
                continue

        if use_eps_growth:
            if eps_growth is None or eps_growth < eps_growth_min or eps_growth > eps_growth_max:
                continue

        ma_s = calc_ma(adj, params["ma_short_p"]).iloc[-1] if len(stock_df) >= params["ma_short_p"] else np.nan
        ma_l = calc_ma(adj, params["ma_long_p"]).iloc[-1] if len(stock_df) >= params["ma_long_p"] else np.nan
        if use_ma_cross:
            if pd.isna(ma_s) or pd.isna(ma_l) or not (ma_s > ma_l):
                continue

        macd_val, sig_val = np.nan, np.nan
        if len(stock_df) >= params["macd_slow"]:
            macd_series, sig_series, _ = calc_macd(adj, fast=params["macd_fast"], slow=params["macd_slow"], signal=params["macd_sig"])
            macd_val = macd_series.iloc[-1]
            sig_val = sig_series.iloc[-1]
        if use_macd_cross:
            if pd.isna(macd_val) or pd.isna(sig_val) or not (macd_val > sig_val):
                continue

        rsi_val = calc_rsi(adj, params["rsi_p"]).iloc[-1] if len(stock_df) >= params["rsi_p"] else np.nan
        if use_rsi:
            if np.isnan(rsi_val) or rsi_val < params["rsi_min"] or rsi_val > params["rsi_max"]:
                continue

        k_val, d_val = np.nan, np.nan
        if len(stock_df) >= params["stoch_k_p"]:
            stoch_k, stoch_d = calc_stoch(stock_df, k=params["stoch_k_p"], d=params["stoch_d_p"], sd=params["stoch_sd_p"])
            k_val = stoch_k.iloc[-1] if not stoch_k.empty else np.nan
            d_val = stoch_d.iloc[-1] if not stoch_d.empty else np.nan
        if use_stoch:
            if np.isnan(k_val) or k_val < params["stoch_min"] or k_val > params["stoch_max"]:
                continue

        prev_close = float(stock_df["AdjC"].iloc[-2])
        chg_pct = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0.0
        mkt_cap_mil = round(mkt_cap / 1e6, 0) if pd.notnull(mkt_cap) and mkt_cap > 0 else None

        results.append({
            "Code": code, "Name": row.get("Name", code), "Market": market,
            "Sector": row.get("Sector", "その他"), "Close": round(price, 1), "前日比(%)": round(chg_pct, 2),
            "PBR": pbr_val, "来期予想EPS": round(feps, 1) if pd.notnull(feps) else None,
            "さ来期予想EPS": round(nxfeps, 1) if pd.notnull(nxfeps) else None,
            "さ来期EPS成長率(%)": eps_growth,
            "来期PER": next_per, "さ来期PER": nx_per,
            "Volume": safe_volume, "MktCap(百万)": mkt_cap_mil, "MA_Short": round(ma_s, 1) if pd.notnull(ma_s) else None,
            "MA_Long": round(ma_l, 1) if pd.notnull(ma_l) else None, "MACD": round(macd_val, 2) if pd.notnull(macd_val) else None,
            "Signal": round(sig_val, 2) if pd.notnull(sig_val) else None,
            "RSI": round(rsi_val, 1) if pd.notnull(rsi_val) and not np.isnan(rsi_val) else None,
            "Stoch_%K": round(k_val, 1) if pd.notnull(k_val) and not np.isnan(k_val) else None,
            "Stoch_%D": round(d_val, 1) if pd.notnull(d_val) and not np.isnan(d_val) else None
        })

    if not results:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(results)

# ===== バックテスト =====
def run_backtest(df, code, sp, start_date=None, end_date=None):
    stock_df = df[df["Code"] == code].sort_values("Date").copy().reset_index(drop=True)
    if len(stock_df) < 30:
        return None, None, stock_df

    adj = stock_df["AdjC"]
    stock_df["MA_Short"] = calc_ma(adj, sp.get("ma_short_p", 5))
    stock_df["MA_Long"] = calc_ma(adj, sp.get("ma_long_p", 25))
    stock_df["RSI"] = calc_rsi(adj, sp.get("rsi_p", 14))

    macd, sig, hist = calc_macd(adj, fast=sp.get("macd_fast", 12), slow=sp.get("macd_slow", 26), signal=sp.get("macd_sig", 9))
    stock_df["MACD"] = macd
    stock_df["Signal"] = sig
    stock_df["Hist"] = hist

    k_line, d_line = calc_stoch(stock_df, k=sp.get("stoch_k_p", 14), d=sp.get("stoch_d_p", 3), sd=sp.get("stoch_sd_p", 3))
    stock_df["Stoch_K"] = k_line
    stock_df["Stoch_D"] = d_line

    if start_date is not None:
        stock_df = stock_df[stock_df["Date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        stock_df = stock_df[stock_df["Date"] <= pd.to_datetime(end_date)]
    stock_df = stock_df.reset_index(drop=True)

    if len(stock_df) < 5:
        return None, None, stock_df

    trades = []
    position = None
    capital = sp.get("capital", 1_000_000)
    initial = capital
    pending_signal = None

    for i in range(1, len(stock_df)):
        row = stock_df.iloc[i]
        prev = stock_df.iloc[i - 1]

        if pending_signal == "BUY" and not position:
            open_price = row["AdjO"]
            shares = int((capital // open_price) // 100) * 100
            if shares > 0:
                position = {"entry_date": row["Date"], "entry_price": open_price, "shares": shares}
                capital -= shares * open_price
            pending_signal = None

        elif pending_signal == "SELL" and position:
            open_price = row["AdjO"]
            profit = (open_price - position["entry_price"]) * position["shares"]
            capital += position["shares"] * open_price
            trades.append({
                "エントリー日": position["entry_date"], "エグジット日": row["Date"],
                "買値": position["entry_price"], "売値": open_price, "株数": position["shares"],
                "損益(円)": round(profit, 0), "リターン(%)": round((open_price / position["entry_price"] - 1) * 100, 2)
            })
            position = None
            pending_signal = None

        if position:
            low_chg = (row["AdjL"] - position["entry_price"]) / position["entry_price"]
            high_chg = (row["AdjH"] - position["entry_price"]) / position["entry_price"]

            if low_chg <= -sp.get("stop_loss", 0.05):
                exit_price = position["entry_price"] * (1 - sp.get("stop_loss", 0.05))
                profit = (exit_price - position["entry_price"]) * position["shares"]
                capital += position["shares"] * exit_price
                trades.append({
                    "エントリー日": position["entry_date"], "エグジット日": row["Date"],
                    "買値": position["entry_price"], "売値": round(exit_price, 1), "株数": position["shares"],
                    "損益(円)": round(profit, 0), "リターン(%)": round(-sp.get("stop_loss", 0.05) * 100, 2)
                })
                position = None
                continue

            elif high_chg >= sp.get("take_profit", 0.10):
                exit_price = position["entry_price"] * (1 + sp.get("take_profit", 0.10))
                profit = (exit_price - position["entry_price"]) * position["shares"]
                capital += position["shares"] * exit_price
                trades.append({
                    "エントリー日": position["entry_date"], "エグジット日": row["Date"],
                    "買値": position["entry_price"], "売値": round(exit_price, 1), "株数": position["shares"],
                    "損益(円)": round(profit, 0), "リターン(%)": round(sp.get("take_profit", 0.10) * 100, 2)
                })
                position = None
                continue

        buy_sig = False
        sell_sig = False

        if sp.get("entry_ma"):
            if pd.notnull(prev["MA_Short"]) and pd.notnull(prev["MA_Long"]) and prev["MA_Short"] <= prev["MA_Long"] and row["MA_Short"] > row["MA_Long"]:
                buy_sig = True

        if sp.get("entry_macd"):
            if pd.notnull(prev["MACD"]) and pd.notnull(prev["Signal"]) and prev["MACD"] <= prev["Signal"] and row["MACD"] > row["Signal"]:
                buy_sig = True

        if sp.get("entry_rsi"):
            if pd.notnull(row["RSI"]) and row["RSI"] < sp.get("rsi_min", 30):
                buy_sig = True

        if sp.get("entry_stoch"):
            if pd.notnull(prev["Stoch_K"]) and pd.notnull(prev["Stoch_D"]) and prev["Stoch_K"] <= prev["Stoch_D"] and row["Stoch_K"] > row["Stoch_D"] and row["Stoch_K"] < sp.get("stoch_min", 25):
                buy_sig = True

        if position:
            if sp.get("exit_ma"):
                if pd.notnull(prev["MA_Short"]) and prev["MA_Long"] and prev["MA_Short"] >= prev["MA_Long"] and row["MA_Short"] < row["MA_Long"]:
                    sell_sig = True

            if sp.get("exit_macd"):
                if pd.notnull(prev["MACD"]) and pd.notnull(prev["Signal"]) and prev["MACD"] >= prev["Signal"] and row["MACD"] < row["Signal"]:
                    sell_sig = True

            if sp.get("exit_rsi"):
                if pd.notnull(row["RSI"]) and row["RSI"] > sp.get("rsi_max", 70):
                    sell_sig = True

            if sp.get("exit_stoch"):
                if pd.notnull(prev["Stoch_K"]) and prev["Stoch_K"] >= prev["Stoch_D"] and row["Stoch_K"] < prev["Stoch_D"] and row["Stoch_K"] > sp.get("stoch_max", 75):
                    sell_sig = True

        if buy_sig and not position:
            pending_signal = "BUY"
        elif sell_sig and position:
            pending_signal = "SELL"

    trades_df = pd.DataFrame(trades)
    summary = {}
    if not trades_df.empty:
        wins = trades_df[trades_df["損益(円)"] > 0]
        final = capital + (position["shares"] * stock_df.iloc[-1]["AdjC"] if position else 0)
        summary = {
            "総トレード数": len(trades_df), "勝率(%)": round(len(wins) / len(trades_df) * 100, 1),
            "総損益(円)": round(trades_df["損益(円)"].sum(), 0), "平均損益(円)": round(trades_df["損益(円)"].mean(), 0),
            "最大利益(円)": round(trades_df["損益(円)"].max(), 0), "最大損失(円)": round(trades_df["損益(円)"].min(), 0),
            "最終資本(円)": round(final, 0), "総リターン(%)": round((final - initial) / initial * 100, 2)
        }

    return trades_df, summary, stock_df

# ===== チャート作成 =====
def create_chart(stock_df, code, name, indicators, ma_short_p=5, ma_long_p=25, macd_fast=12, macd_slow=26, macd_sig=9, rsi_p=14, stoch_k_p=14, stoch_d_p=3, stoch_sd_p=3, show_vol=True, height=420):
    sub_indicators = [ind for ind in ["RSI", "MACD", "STOCH"] if ind in indicators]
    rows = 1 + (1 if show_vol else 0) + len(sub_indicators)
    heights = [0.5]
    if show_vol:
        heights.append(0.15)
    for _ in sub_indicators:
        heights.append(0.15)

    total_h = sum(heights)
    heights = [h / total_h for h in heights]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=heights, vertical_spacing=0.03)

    fig.add_trace(
        go.Candlestick(
            x=stock_df["Date"], open=stock_df["AdjO"], high=stock_df["AdjH"], low=stock_df["AdjL"], close=stock_df["AdjC"],
            name="価格", increasing=dict(line=dict(color="#18181b", width=1), fillcolor="#ffffff"),
            decreasing=dict(line=dict(color="#18181b", width=1), fillcolor="#18181b")
        ), row=1, col=1
    )

    adj = stock_df["AdjC"]
    if "MA_Short" in indicators:
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=calc_ma(adj, ma_short_p), name=f"MA{ma_short_p}", line=dict(color="#f97316", width=1.2)), row=1, col=1)
    if "MA_Long" in indicators:
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=calc_ma(adj, ma_long_p), name=f"MA{ma_long_p}", line=dict(color="#06b6d4", width=1.2)), row=1, col=1)
    if "MA75" in indicators:
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=calc_ma(adj, 75), name="MA75", line=dict(color="#84cc16", width=1.2)), row=1, col=1)
    if "BB" in indicators:
        upper, _, lower = calc_bollinger(adj)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=upper, name="BB上", line=dict(color="#a78bfa", dash="dash", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=lower, name="BB下", line=dict(color="#a78bfa", dash="dash", width=1), fill="tonexty", fillcolor="rgba(167,139,250,0.08)"), row=1, col=1)

    cur_row = 2
    if show_vol:
        vol_col = "AdjVo" if "AdjVo" in stock_df.columns else "Volume"
        fig.add_trace(go.Bar(x=stock_df["Date"], y=stock_df[vol_col], name="出来高", marker_color="#86efac", opacity=0.75), row=cur_row, col=1)
        cur_row += 1

    if "RSI" in indicators:
        rsi = calc_rsi(adj, rsi_p)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=rsi, name=f"RSI({rsi_p})", line=dict(color="#c084fc", width=1.2)), row=cur_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=cur_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", line_width=1, row=cur_row, col=1)
        cur_row += 1

    if "MACD" in indicators:
        macd, sig, hist = calc_macd(adj, fast=macd_fast, slow=macd_slow, signal=macd_sig)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=macd, name="MACD", line=dict(color="#60a5fa", width=1.2)), row=cur_row, col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=sig, name="Sig", line=dict(color="#f87171", width=1.2)), row=cur_row, col=1)
        bar_colors = ["#ef4444" if v >= 0 else "#3b82f6" for v in hist]
        fig.add_trace(go.Bar(x=stock_df["Date"], y=hist, name="Hist", marker_color=bar_colors, opacity=0.7), row=cur_row, col=1)
        cur_row += 1

    if "STOCH" in indicators:
        k_line, d_line = calc_stoch(stock_df, k=stoch_k_p, d=stoch_d_p, sd=stoch_sd_p)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=k_line, name="%K", line=dict(color="#fbbf24", width=1.2)), row=cur_row, col=1)
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=d_line, name="%D", line=dict(color="#f472b6", width=1.2)), row=cur_row, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", line_width=1, row=cur_row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#22c55e", line_width=1, row=cur_row, col=1)

    fig.update_layout(
        title=dict(text=f"<b>{code}</b> {name}", font=dict(size=14)),
        height=height, xaxis_rangeslider_visible=False, template="plotly_dark",
        margin=dict(l=20, r=20, t=35, b=20), showlegend=False
    )
    return fig

# ===== ニュース＆決算開示リサーチ =====
@st.cache_data(ttl=1800)
def fetch_stock_news(code, name):
    query = f"{name} {code[:4]} 株"
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
    news_items = []
    try:
        resp = requests.get(rss_url, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:4]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                clean_title = title.split(" - ")[0].strip() if title else ""
                news_items.append({"title": clean_title, "link": link, "date": pub_date[:16]})
    except Exception:
        pass
    return news_items

@st.cache_data(ttl=3600)
def fetch_earnings_calendar(code):
    headers = {"x-api-key": API_KEY}
    url = f"{API_BASE}/equities/earnings-calendar"
    c_str = str(code).strip()
    c5 = f"{c_str[:4]}0" if len(c_str) == 4 else c_str
    try:
        resp = requests.get(url, headers=headers, params={"code": c5}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data") or data.get("earnings_calendar") or []
            if items:
                return items[-1].get("Date") or items[-1].get("AnnouncementDate")
    except Exception:
        pass
    return "未定 / 発表なし"

# ===== サイドバー =====
with st.sidebar:
    st.markdown("### 🗂️ データ管理")
    csv_files = get_csv_files()
    if not csv_files:
        st.error("CSVファイルが見つかりません。リポジトリに CSV ファイルが存在するか確認してください。")
        st.stop()

    csv_labels = [os.path.basename(f) for f in csv_files]
    sel_label = st.selectbox("📂 データファイル", csv_labels, index=0)
    csv_path = csv_files[csv_labels.index(sel_label)]

    if st.button("🚀 最新データ取得", use_container_width=True):
        with st.spinner("データ取得中..."):
            try:
                fetch_script = os.path.join(DATA_DIR, "fetch_clean_db.py")
                if not os.path.exists(fetch_script):
                    st.warning("クラウド上では手動ファイル更新またはAPI直接更新を推奨します。")
                else:
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"
                    r = subprocess.run(
                        [CURRENT_PYTHON, fetch_script], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", env=env, timeout=300
                    )
                    if r.returncode == 0:
                        st.success("✅ 取得完了！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(r.stderr[:400] if r.stderr else "取得に失敗しました")
            except Exception as e:
                st.error(str(e))

    st.divider()

    st.markdown("### 🏛️ 対象市場")
    selected_markets = st.multiselect("対象市場を選択（複数可）", options=["東証全部", "プライム", "スタンダード", "グロース", "ETF"], default=["東証全部"])

    st.divider()

    st.markdown("### 🔍 スクリーニング条件")
    
    with st.expander("💹 財務・バリュエーション条件", expanded=True):
        use_pbr = st.checkbox("現在のPBR 上限フィルタを適用", value=False)
        pbr_max = st.slider("PBR 上限値（倍）", min_value=0.5, max_value=5.0, value=1.5, step=0.1) if use_pbr else 1.5

        use_eps_growth = st.checkbox("さ来期EPS / 来期EPS 成長率を適用", value=False)
        eps_growth_range = st.slider(
            "さ来期EPS成長率(%)（例: +100%＝さ来期利益2倍）",
            min_value=-50.0, max_value=1000.0, value=(0.0, 150.0), step=5.0
        ) if use_eps_growth else (-50.0, 1000.0)

    with st.expander("基本フィルタ", expanded=True):
        use_vol = st.checkbox("出来高フィルタ", value=False)
        vol_min = st.number_input("最小出来高", value=10_000, step=10_000) if use_vol else 0
        use_mktcap = st.checkbox("時価総額フィルタ", value=False)
        mktcap_min = st.number_input("最小時価総額(百万円)", value=1_000, step=100) * 1e6 if use_mktcap else 0

    with st.expander("移動平均（MA）条件", expanded=False):
        use_ma_cross = st.checkbox("短期MA > 長期MA を適用", value=False)
        ma_short_p = st.slider("短期MA 期間", 3, 20, 5)
        ma_long_p = st.slider("長期MA 期間", 10, 75, 25)

    with st.expander("MACD 条件", expanded=False):
        use_macd_cross = st.checkbox("MACD > シグナル を適用", value=False)
        c_m1, c_m2, c_m3 = st.columns(3)
        macd_fast = c_m1.number_input("Fast(短期)", value=12, min_value=2, max_value=50, step=1)
        macd_slow = c_m2.number_input("Slow(長期)", value=26, min_value=5, max_value=100, step=1)
        macd_sig = c_m3.number_input("Signal", value=9, min_value=1, max_value=30, step=1)

    with st.expander("RSI 条件", expanded=False):
        use_rsi = st.checkbox("RSIフィルタを適用", value=False)
        rsi_p = st.slider("RSI 計算期間", 5, 30, 14)
        rsi_range = st.slider("RSI 範囲 (最小=売られすぎ, 最大=買われすぎ)", 0, 100, (30, 70))

    with st.expander("ストキャスティクス 条件", expanded=False):
        use_stoch = st.checkbox("ストキャスフィルタを適用", value=False)
        stoch_k_p = st.slider("Slow %K 期間", 5, 25, 14)
        stoch_d_p = st.slider("Slow %D 期間", 2, 10, 3)
        stoch_sd_p = st.slider("SD 期間", 2, 10, 3)
        stoch_range = st.slider("%K 範囲 (最小=売られすぎ, 最大=買われすぎ)", 0, 100, (25, 75))

    do_screen = st.button("🔍 スクリーニング実行", type="primary", use_container_width=True)

    st.divider()

    st.markdown("### 📊 チャート表示指標")
    ind_ma_s = st.checkbox(f"📈 短期MA ({ma_short_p})", value=True)
    ind_ma_l = st.checkbox(f"📈 長期MA ({ma_long_p})", value=True)
    ind_ma75 = st.checkbox("📈 MA75", value=False)
    ind_bb = st.checkbox("📉 ボリンジャーバンド", value=False)
    ind_rsi = st.checkbox(f"🔵 RSI ({rsi_p})", value=True)
    ind_macd = st.checkbox(f"🟡 MACD ({macd_fast}, {macd_slow}, {macd_sig})", value=True)
    ind_stoch = st.checkbox(f"🔴 ストキャス ({stoch_k_p},{stoch_d_p},{stoch_sd_p})", value=False)
    ind_vol = st.checkbox("📊 出来高", value=True)

    indicators = (
        (["MA_Short"] if ind_ma_s else []) + (["MA_Long"] if ind_ma_l else []) +
        (["MA75"] if ind_ma75 else []) + (["BB"] if ind_bb else []) +
        (["RSI"] if ind_rsi else []) + (["MACD"] if ind_macd else []) + (["STOCH"] if ind_stoch else [])
    )

    st.divider()

    st.markdown("### 🔬 バックテスト設定")
    bt_period_mode = st.selectbox("検証期間", ["全期間", "直近1年", "直近6ヶ月", "直近3ヶ月", "日付指定"])
    start_d, end_d = None, None

    df_temp = load_csv(csv_path)
    min_date = df_temp["Date"].min().date()
    max_date = df_temp["Date"].max().date()

    if bt_period_mode == "直近1年":
        start_d = max_date - timedelta(days=365)
    elif bt_period_mode == "直近6ヶ月":
        start_d = max_date - timedelta(days=180)
    elif bt_period_mode == "直近3ヶ月":
        start_d = max_date - timedelta(days=90)
    elif bt_period_mode == "日付指定":
        d_range = st.date_input("期間選択", [min_date, max_date], min_value=min_date, max_value=max_date)
        if isinstance(d_range, (list, tuple)) and len(d_range) == 2:
            start_d, end_d = d_range[0], d_range[1]

    capital = st.number_input("初期資金(円)", value=1_000_000, step=100_000)
    take_profit = st.slider("利確(%)", 1, 50, 10) / 100
    stop_loss = st.slider("損切(%)", 1, 30, 5) / 100

    st.markdown("##### 🚀 エントリー条件")
    entry_ma = st.checkbox(f"短期MA({ma_short_p}) > 長期MA({ma_long_p}) GC", value=True)
    entry_macd_bt = st.checkbox(f"MACD > Sig GC", value=False)
    entry_rsi_bt = st.checkbox(f"RSI < {rsi_range[0]}（売られすぎ）", value=False)
    entry_stoch_bt = st.checkbox(f"ストキャスGC かつ %K < {stoch_range[0]}", value=False)

    st.markdown("##### 🏁 エグジット条件")
    exit_ma = st.checkbox(f"短期MA({ma_short_p}) < 長期MA({ma_long_p}) DC", value=True)
    exit_macd_bt = st.checkbox(f"MACD < Sig DC", value=False)
    exit_rsi_bt = st.checkbox(f"RSI > {rsi_range[1]}（買われすぎ）", value=False)
    exit_stoch_bt = st.checkbox(f"ストキャスDC かつ %K > {stoch_range[1]}", value=False)

# ========================================================
# ===== メインエリア =====
# ========================================================
df = load_csv(csv_path)

st.markdown("<h1 style='margin-bottom:0'>📈 株式分析・スクリーニングシステム</h1>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("📁 データファイル", sel_label[:20] + "…")
m2.metric("📈 登録銘柄数", f"{df['Code'].nunique():,} 銘柄")
m3.metric("📅 データ期間", f"{df['Date'].min().date()} ～ {df['Date'].max().date()}")
m4.metric("📋 総レコード数", f"{len(df):,} 件")

st.divider()

if "selected_codes" not in st.session_state:
    st.session_state.selected_codes = []

params = {
    "target_markets": selected_markets if selected_markets else ["東証全部"],
    "use_pbr": use_pbr, "pbr_max": pbr_max,
    "use_eps_growth": use_eps_growth,
    "eps_growth_min": eps_growth_range[0],
    "eps_growth_max": eps_growth_range[1],
    "use_vol": use_vol, "vol_min": vol_min, "use_mktcap": use_mktcap, "mktcap_min": mktcap_min,
    "use_ma_cross": use_ma_cross, "ma_short_p": ma_short_p, "ma_long_p": ma_long_p,
    "use_macd_cross": use_macd_cross, "macd_fast": macd_fast, "macd_slow": macd_slow, "macd_sig": macd_sig,
    "use_rsi": use_rsi, "rsi_p": rsi_p, "rsi_min": rsi_range[0], "rsi_max": rsi_range[1],
    "use_stoch": use_stoch, "stoch_k_p": stoch_k_p, "stoch_d_p": stoch_d_p, "stoch_sd_p": stoch_sd_p,
    "stoch_min": stoch_range[0], "stoch_max": stoch_range[1]
}

if "scr_result" not in st.session_state or do_screen or st.session_state.scr_result is None:
    with st.spinner("スクリーニング計算中..."):
        st.session_state.scr_result = run_screening(df, params)

scr_df = st.session_state.scr_result

# ===== 銘柄一覧 ＆ リアルタイム検索バー UI =====
st.markdown('<div class="step-header"><h3>📋 銘柄スクリーニング・検索結果一覧</h3></div>', unsafe_allow_html=True)

f_col1, f_col2, f_col3 = st.columns([2.5, 1.8, 1.8])
with f_col1:
    search_query = st.text_input("🔎 銘柄コードまたは社名で検索", placeholder="例: 7203, トヨタ, 9984, ソニー, 1419")
with f_col2:
    all_sectors = ["全業種"] + sorted([s for s in scr_df["Sector"].dropna().unique() if s != "" and s != "その他"]) + ["その他"]
    selected_sector = st.selectbox("🏢 業種で絞り込み", all_sectors)
with f_col3:
    sort_by = st.selectbox("🔃 並び替え（ソート）", [
        "コード順 (昇順)", "さ来期EPS成長率 (高い順=急成長)", "PBR (低い順)", "前日比 (上昇率順)", "出来高 (多い順)"
    ])

filtered_df = scr_df.copy()

if search_query:
    q = search_query.strip().upper()
    filtered_df = filtered_df[
        filtered_df["Code"].str.upper().str.contains(q, na=False) | 
        filtered_df["Name"].str.upper().str.contains(q, na=False)
    ]

if selected_sector != "全業種":
    filtered_df = filtered_df[filtered_df["Sector"] == selected_sector]

if sort_by == "コード順 (昇順)":
    filtered_df = filtered_df.sort_values("Code", ascending=True)
elif sort_by == "さ来期EPS成長率 (高い順=急成長)":
    filtered_df = filtered_df.sort_values("さ来期EPS成長率(%)", ascending=False, na_position="last")
elif sort_by == "PBR (低い順)":
    filtered_df = filtered_df.sort_values("PBR", ascending=True, na_position="last")
elif sort_by == "前日比 (上昇率順)":
    filtered_df = filtered_df.sort_values("前日比(%)", ascending=False)
elif sort_by == "出来高 (多い順)":
    filtered_df = filtered_df.sort_values("Volume", ascending=False)

st.caption(f"💡 表示件数: **{len(filtered_df):,} 銘柄** / 全 {len(scr_df):,} 銘柄中（比較したい銘柄にチェックを入れてください / **最大3銘柄**）")

if filtered_df.empty:
    st.warning("⚠️ 該当する銘柄が見つかりませんでした。条件を変更してください。")
else:
    scr_display = filtered_df.copy()
    scr_display.insert(0, "選択", scr_display["Code"].isin(st.session_state.selected_codes))

    edited = st.data_editor(
        scr_display,
        column_config={
            "選択": st.column_config.CheckboxColumn("選択", default=False),
            "Close": st.column_config.NumberColumn("株価(円)", format="¥%.1f"),
            "前日比(%)": st.column_config.NumberColumn("前日比", format="%.2f%%"),
            "PBR": st.column_config.NumberColumn("PBR(倍)", format="%.2f"),
            "来期予想EPS": st.column_config.NumberColumn("来期予想EPS", format="¥%.1f"),
            "さ来期予想EPS": st.column_config.NumberColumn("さ来期予想EPS", format="¥%.1f"),
            "さ来期EPS成長率(%)": st.column_config.NumberColumn("さ来期EPS成長率", format="%.2f%%"),
            "来期PER": st.column_config.NumberColumn("来期PER", format="%.1f倍"),
            "さ来期PER": st.column_config.NumberColumn("さ来期PER", format="%.1f倍"),
            "Volume": st.column_config.NumberColumn("出来高", format="%d"),
            "MktCap(百万)": st.column_config.NumberColumn("時価総額(百万)", format="%.0f"),
        },
        use_container_width=True, hide_index=True, key="stock_selector"
    )
    selected = edited[edited["選択"] == True]["Code"].tolist()
    st.session_state.selected_codes = selected

    if not selected:
        st.info("👆 表内のチェックボックス（最大3銘柄）を選択すると、下にチャート・3列バックテスト・財務指標・ニュースが表示されます。")
    else:
        target_codes = selected[:3]
        if len(selected) > 3:
            st.warning(f"現在 {len(selected)} 銘柄選択されています。先頭3銘柄（{', '.join(target_codes)}）を表示します。")

        # 1. チャート
        st.markdown('<div class="step-header"><h3>📈 銘柄チャート比較</h3></div>', unsafe_allow_html=True)
        chart_cols = st.columns(len(target_codes))
        for i, code in enumerate(target_codes):
            with chart_cols[i]:
                code_row = scr_df[scr_df["Code"] == code]
                name = code_row["Name"].values[0] if not code_row.empty and pd.notnull(code_row["Name"].values[0]) else code
                sdf = df[df["Code"] == code].sort_values("Date")
                st.plotly_chart(
                    create_chart(
                        sdf, code, name, indicators, ma_short_p=ma_short_p, ma_long_p=ma_long_p,
                        macd_fast=macd_fast, macd_slow=macd_slow, macd_sig=macd_sig,
                        rsi_p=rsi_p, stoch_k_p=stoch_k_p, stoch_d_p=stoch_d_p, stoch_sd_p=stoch_sd_p,
                        show_vol=ind_vol, height=380
                    ), use_container_width=True
                )

        # 2. バックテスト
        st.markdown('<div class="step-header"><h3>🔬 バックテスト結果（3銘柄比較）</h3></div>', unsafe_allow_html=True)
        sp = {
            "capital": capital, "take_profit": take_profit, "stop_loss": stop_loss,
            "entry_ma": entry_ma, "entry_macd": entry_macd_bt, "entry_rsi": entry_rsi_bt, "entry_stoch": entry_stoch_bt,
            "exit_ma": exit_ma, "exit_macd": exit_macd_bt, "exit_rsi": exit_rsi_bt, "exit_stoch": exit_stoch_bt,
            "ma_short_p": ma_short_p, "ma_long_p": ma_long_p, "macd_fast": macd_fast, "macd_slow": macd_slow, "macd_sig": macd_sig,
            "rsi_p": rsi_p, "rsi_min": rsi_range[0], "rsi_max": rsi_range[1],
            "stoch_k_p": stoch_k_p, "stoch_d_p": stoch_d_p, "stoch_sd_p": stoch_sd_p, "stoch_min": stoch_range[0], "stoch_max": stoch_range[1]
        }

        bt_cols = st.columns(len(target_codes))
        for i, code in enumerate(target_codes):
            with bt_cols[i]:
                code_row = scr_df[scr_df["Code"] == code]
                name = code_row["Name"].values[0] if not code_row.empty and pd.notnull(code_row["Name"].values[0]) else code
                st.markdown(f"#### 📊 {code} {name}")
                trades_df, summary, _ = run_backtest(df, code, sp, start_date=start_d, end_date=end_d)

                if summary:
                    st.markdown(f"""
                    <div class="metric-box">
                        <b>勝率:</b> {summary['勝率(%)']}% ({summary['総トレード数']}回)<br>
                        <b>総損益:</b> <span class="{'positive' if summary['総損益(円)'] > 0 else 'negative'}">{summary['総損益(円)']:+,.0f} 円 ({summary['総リターン(%)']:+.2f}%)</span><br>
                        <b>平均損益:</b> {summary['平均損益(円)']:+,.0f} 円<br>
                        <b>最大利益 / 損失:</b> {summary['最大利益(円)']:+,.0f} / {summary['最大損失(円)']:+,.0f}
                    </div>
                    """, unsafe_allow_html=True)
                    if trades_df is not None and not trades_df.empty:
                        colors = ["#ef4444" if p > 0 else "#3b82f6" for p in trades_df["損益(円)"]]
                        fig_pnl = go.Figure(go.Bar(x=trades_df["エグジット日"].astype(str), y=trades_df["損益(円)"], marker_color=colors))
                        fig_pnl.update_layout(title="個別損益(円)", template="plotly_dark", height=200, margin=dict(l=10, r=10, t=30, b=20))
                        st.plotly_chart(fig_pnl, use_container_width=True)
                else:
                    st.warning("取引が発生しませんでした。")

        # 3. ファンダメンタルズ（最新確定値・予想値同期）
        st.markdown('<div class="step-header"><h3>💹 ファンダメンタルズ情報（J-Quants V2 API）</h3></div>', unsafe_allow_html=True)
        funda_cols = st.columns(len(target_codes))
        for i, code in enumerate(target_codes):
            with funda_cols[i]:
                code_row = scr_df[scr_df["Code"] == code]
                name = code_row["Name"].values[0] if not code_row.empty and pd.notnull(code_row["Name"].values[0]) else code
                st.markdown(f"#### 🏢 {code} {name}")
                target_stock = df[df["Code"] == code]
                current_price = float(target_stock["AdjC"].iloc[-1]) if not target_stock.empty else 0.0
                funda = fetch_fundamental_v2(code, current_price)

                if funda is None:
                    st.info("財務データが見つかりませんでした。")
                else:
                    m1, m2 = st.columns(2)
                    m1.metric("実績PER", f"{funda['PER(倍)']}倍" if funda["PER(倍)"] else "N/A")
                    m2.metric("PBR", f"{funda['PBR(倍)']}倍" if funda["PBR(倍)"] else "N/A")

                    m3, m4 = st.columns(2)
                    m3.metric("来期予想EPS", f"¥{funda['来期予想EPS(円)']}" if funda["来期予想EPS(円)"] else "N/A")
                    m4.metric("さ来期予想EPS", f"¥{funda['さ来期予想EPS(円)']}" if funda["さ来期予想EPS(円)"] else "N/A")

                    m5, m6 = st.columns(2)
                    growth_val = funda["さ来期EPS成長率(%)"]
                    m5.metric(
                        "さ来期EPS増加率",
                        f"{growth_val:+.2f}%" if growth_val is not None else "N/A",
                        delta=f"{growth_val:+.2f}%" if growth_val is not None else None
                    )
                    m6.metric("来期予想PER", f"{funda['来期PER(倍)']}倍" if funda["来期PER(倍)"] else "N/A")

                    m7, m8 = st.columns(2)
                    m7.metric("ROE", f"{funda['ROE(%)']}%" if funda["ROE(%)"] else "N/A")
                    m8.metric("配当利回り", f"{funda['配当利回り(%)']}%" if funda["配当利回り(%)"] else "N/A")

        # 4. ニュース＆決算予定
        st.markdown('<div class="step-header"><h3>📰 銘柄リサーチ＆最新材料</h3></div>', unsafe_allow_html=True)
        research_cols = st.columns(len(target_codes))
        for i, code in enumerate(target_codes):
            with research_cols[i]:
                code_row = scr_df[scr_df["Code"] == code]
                name = code_row["Name"].values[0] if not code_row.empty and pd.notnull(code_row["Name"].values[0]) else code
                st.markdown(f"#### 🔍 {code} {name}")
                next_earnings = fetch_earnings_calendar(code)
                st.info(f"📅 **次回決算発表予定:** {next_earnings}")
                news_list = fetch_stock_news(code, name)
                if news_list:
                    st.markdown("**📌 最新ヘッドライン:**")
                    for n in news_list:
                        st.markdown(f"- [{n['title']}]({n['link']}) <span style='font-size:0.8em;color:#888;'>({n['date']})</span>", unsafe_allow_html=True)
                else:
                    st.caption("直近のヘッドラインニュースは見つかりませんでした。")
>>>>>>> cf2cfd1c60e9439a49b21414de0c63423cedc283
