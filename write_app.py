# write_app.py - app.pyを新しく書き直すスクリプト

content = '''
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

# ページ設定
st.set_page_config(page_title="株式スクリーニング", layout="wide")

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
API_BASE = "https://api.jquants.com/v2"
CSV_DIR = "C:/stock_system"
VENV_PYTHON = "C:/stock_system/venv/Scripts/python.exe"

def get_latest_csv():
    files = glob.glob(os.path.join(CSV_DIR, "stocks_OHLC_*.csv"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def load_data(filepath):
    try:
        df = pd.read_csv(filepath, dtype={"Code": str})
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None

def get_fundamental_data(code, current_price):
    try:
        url = f"{API_BASE}/fins/summary"
        headers = {"X-API-KEY": API_KEY}
        params = {"code": code}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return None
        data = response.json()
        items = data.get("summary", [])
        if not items:
            return None
        item = items[0]
        eps = item.get("EPS", None)
        bps = item.get("BPS", None)
        roe = item.get("ROE", None)
        per = round(current_price / eps, 2) if eps and eps != 0 else None
        pbr = round(current_price / bps, 2) if bps and bps != 0 else None
        return {
            "PER": per,
            "PBR": pbr,
            "ROE": roe,
            "EPS": eps,
            "BPS": bps,
            "売上高": item.get("Sales", None),
            "営業利益": item.get("OP", None),
            "純利益": item.get("NP", None),
        }
    except Exception as e:
        return None

# サイドバー
st.sidebar.title("⚙️ コントロール")

if st.sidebar.button("📥 データ更新"):
    with st.spinner("データ取得中..."):
        result = subprocess.run(
            [VENV_PYTHON, "C:/stock_system/fetch_3months.py"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            st.sidebar.success("データ取得完了！")
        else:
            st.sidebar.error(f"エラー: {result.stderr[:200]}")

if st.sidebar.button("🔧 データ修正"):
    with st.spinner("データ修正中..."):
        result = subprocess.run(
            [VENV_PYTHON, "C:/stock_system/fix_data.py"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            st.sidebar.success("データ修正完了！")
        else:
            st.sidebar.error(f"エラー: {result.stderr[:200]}")

st.sidebar.markdown("---")

# CSVファイル選択
csv_files = sorted(
    glob.glob(os.path.join(CSV_DIR, "stocks_OHLC_*.csv")),
    key=os.path.getmtime, reverse=True
)
csv_names = [os.path.basename(f) for f in csv_files]
selected_csv_name = st.sidebar.selectbox("📂 データファイル選択", csv_names)
selected_csv = os.path.join(CSV_DIR, selected_csv_name) if selected_csv_name else get_latest_csv()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 スクリーニング条件")

min_price = st.sidebar.number_input("最低株価", value=500, step=100)
max_price = st.sidebar.number_input("最高株価", value=5000, step=100)
min_volume = st.sidebar.number_input("最低出来高", value=100000, step=10000)
lookback = st.sidebar.slider("移動平均期間(日)", 5, 60, 25)
screen_btn = st.sidebar.button("🔍 スクリーニング実行")

st.sidebar.markdown("---")
st.sidebar.subheader("📈 テクニカル指標")
show_ma = st.sidebar.checkbox("移動平均線", value=True)
show_bb = st.sidebar.checkbox("ボリンジャーバンド", value=False)
show_rsi = st.sidebar.checkbox("RSI", value=False)
show_macd = st.sidebar.checkbox("MACD", value=False)

# メインエリア
st.title("📈 株式スクリーニング＆分析システム")

df = load_data(selected_csv)

if df is None:
    st.error("データを読み込めませんでした。")
    st.stop()

st.success(f"✅ データ読み込み完了: {len(df):,}件 | {os.path.basename(selected_csv)}")

# スクリーニング実行
if screen_btn:
    with st.spinner("スクリーニング中..."):
        latest_date = df["Date"].max()
        latest_df = df[df["Date"] == latest_date].copy()

        col_close = "AdjC" if "AdjC" in latest_df.columns else "Close"
        col_volume = "AdjVo" if "AdjVo" in latest_df.columns else "Volume"

        filtered = latest_df[
            (latest_df[col_close] >= min_price) &
            (latest_df[col_close] <= max_price) &
            (latest_df[col_volume] >= min_volume)
        ].copy()

        # 移動平均フィルター
        results = []
        for code in filtered["Code"].unique():
            stock_df = df[df["Code"] == code].sort_values("Date").tail(lookback + 10)
            if len(stock_df) < lookback:
                continue
            close = stock_df[col_close].values
            ma = close[-lookback:].mean()
            current = close[-1]
            if current > ma:
                row = filtered[filtered["Code"] == code].iloc[0]
                results.append({
                    "コード": code,
                    "銘柄名": row.get("Name", ""),
                    "セクター": row.get("Sector", ""),
                    "現在値": current,
                    "移動平均": round(ma, 1),
                    "乖離率(%)": round((current - ma) / ma * 100, 2),
                    "出来高": int(row[col_volume]),
                })

        st.session_state["screen_results"] = results
        st.session_state["screen_date"] = latest_date
        st.session_state["col_close"] = col_close
        st.session_state["col_volume"] = col_volume

# 結果表示
if "screen_results" in st.session_state:
    results = st.session_state["screen_results"]
    st.subheader(f"🔍 スクリーニング結果: {st.session_state[\'screen_date\'].strftime(\'%Y-%m-%d\')} 時点")

    if not results:
        st.warning("条件に合う銘柄がありませんでした。")
    else:
        result_df = pd.DataFrame(results)
        st.dataframe(result_df, use_container_width=True)
        st.info(f"該当銘柄数: {len(result_df)}件")

        selected_code = st.selectbox(
            "📊 チャートを表示する銘柄を選択",
            result_df["コード"].tolist(),
            format_func=lambda x: f"{x} {result_df[result_df[\'コード\']==x][\'銘柄名\'].values[0]}"
        )

        if selected_code:
            stock_data = df[df["Code"] == selected_code].sort_values("Date").tail(120)
            col_close = st.session_state.get("col_close", "AdjC")
            col_volume = st.session_state.get("col_volume", "AdjVo")

            # チャート作成
            rows = 2
            row_heights = [0.7, 0.3]
            if show_rsi:
                rows += 1
                row_heights.append(0.2)
            if show_macd:
                rows += 1
                row_heights.append(0.2)

            fig = make_subplots(
                rows=rows, cols=1,
                shared_xaxes=True,
                row_heights=row_heights,
                vertical_spacing=0.03
            )

            # ローソク足
            fig.add_trace(go.Candlestick(
                x=stock_data["Date"],
                open=stock_data["AdjO"] if "AdjO" in stock_data.columns else stock_data["Open"],
                high=stock_data["AdjH"] if "AdjH" in stock_data.columns else stock_data["High"],
                low=stock_data["AdjL"] if "AdjL" in stock_data.columns else stock_data["Low"],
                close=stock_data[col_close],
                name="株価"
            ), row=1, col=1)

            if show_ma:
                for period in [25, 75]:
                    ma_vals = stock_data[col_close].rolling(period).mean()
                    fig.add_trace(go.Scatter(
                        x=stock_data["Date"], y=ma_vals,
                        name=f"MA{period}", line=dict(width=1)
                    ), row=1, col=1)

            if show_bb:
                ma20 = stock_data[col_close].rolling(20).mean()
                std20 = stock_data[col_close].rolling(20).std()
                fig.add_trace(go.Scatter(x=stock_data["Date"], y=ma20+2*std20, name="BB+2σ", line=dict(dash="dash", width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=stock_data["Date"], y=ma20-2*std20, name="BB-2σ", line=dict(dash="dash", width=1)), row=1, col=1)

            # 出来高
            fig.add_trace(go.Bar(
                x=stock_data["Date"], y=stock_data[col_volume],
                name="出来高", marker_color="lightblue"
            ), row=2, col=1)

            current_row = 3
            if show_rsi:
                delta = stock_data[col_close].diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                fig.add_trace(go.Scatter(x=stock_data["Date"], y=rsi, name="RSI", line=dict(color="purple")), row=current_row, col=1)
                current_row += 1

            if show_macd:
                ema12 = stock_data[col_close].ewm(span=12).mean()
                ema26 = stock_data[col_close].ewm(span=26).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9).mean()
                fig.add_trace(go.Scatter(x=stock_data["Date"], y=macd, name="MACD", line=dict(color="blue")), row=current_row, col=1)
                fig.add_trace(go.Scatter(x=stock_data["Date"], y=signal, name="Signal", line=dict(color="red")), row=current_row, col=1)

            name_val = result_df[result_df["コード"]==selected_code]["銘柄名"].values[0]
            fig.update_layout(
                title=f"{selected_code} {name_val}",
                height=700,
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

            # ファンダメンタル表示
            st.subheader("📋 ファンダメンタル情報")
            current_price = float(stock_data[col_close].iloc[-1])
            with st.spinner("ファンダメンタルデータ取得中..."):
                fund = get_fundamental_data(selected_code, current_price)
            if fund:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("PER", f"{fund[\'PER\']}倍" if fund[\'PER\'] else "N/A")
                col2.metric("PBR", f"{fund[\'PBR\']}倍" if fund[\'PBR\'] else "N/A")
                col3.metric("ROE", f"{fund[\'ROE\']}%" if fund[\'ROE\'] else "N/A")
                col4.metric("EPS", f"{fund[\'EPS\']}円" if fund[\'EPS\'] else "N/A")
                col1b, col2b, col3b = st.columns(3)
                col1b.metric("売上高", f"{fund[\'売上高\']:,}" if fund[\'売上高\'] else "N/A")
                col2b.metric("営業利益", f"{fund[\'営業利益\']:,}" if fund[\'営業利益\'] else "N/A")
                col3b.metric("純利益", f"{fund[\'純利益\']:,}" if fund[\'純利益\'] else "N/A")
            else:
                st.info("ファンダメンタルデータを取得できませんでした。")
'''

with open("C:/stock_system/app.py", "w", encoding="utf-8") as f:
    f.write(content.strip())

print("app.py を正常に書き込みました！")