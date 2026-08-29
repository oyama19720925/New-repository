import streamlit as st
import pandas as pd
import numpy as np
import glob
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = "MS Gothic"

st.title("株式スクリーニングシステム")

files = sorted(glob.glob("stocks_OHLC_*.csv"), reverse=True)
if not files:
    st.error("CSVファイルが見つかりません")
    st.stop()

selected_file = st.selectbox("データファイル選択", files)

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, low_memory=False)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data(selected_file)
st.success(f"データ読込完了: {len(df)}行")

st.sidebar.header("スクリーニング条件")
use_ma = st.sidebar.checkbox("移動平均ゴールデンクロス", value=True)
ma_short = st.sidebar.number_input("短期MA", value=5, min_value=1)
ma_long = st.sidebar.number_input("長期MA", value=25, min_value=1)

use_rsi = st.sidebar.checkbox("RSI", value=False)
rsi_period = st.sidebar.number_input("RSI期間", value=14, min_value=1)
rsi_min = st.sidebar.number_input("RSI最小値", value=30.0)
rsi_max = st.sidebar.number_input("RSI最大値", value=70.0)

use_stoch = st.sidebar.checkbox("ストキャスティクス", value=False)
stoch_k = st.sidebar.number_input("%K期間", value=14, min_value=1)
stoch_d = st.sidebar.number_input("%D期間", value=3, min_value=1)
stoch_min = st.sidebar.number_input("ストキャス最小値", value=20.0)
stoch_max = st.sidebar.number_input("ストキャス最大値", value=80.0)
use_stoch_gc = st.sidebar.checkbox("%Kが%Dをゴールデンクロス", value=False)

use_bb = st.sidebar.checkbox("ボリンジャーバンド", value=False)
bb_period = st.sidebar.number_input("BB期間", value=20, min_value=1)
bb_sigma = st.sidebar.number_input("BBシグマ", value=2.0)

if st.sidebar.button("スクリーニング実行"):
    results = []
    codes = df["Code"].unique()
    progress = st.progress(0)

    for i, code in enumerate(codes):
        stock = df[df["Code"] == code].sort_values("Date").copy()
        min_len = max(int(ma_long), int(rsi_period), int(stoch_k)+int(stoch_d), int(bb_period)) + 5
        if len(stock) < min_len:
            continue

        close = stock["C"]
        high = stock["H"]
        low = stock["L"]
        name = stock["CoName"].iloc[-1] if "CoName" in stock.columns else ""
        sector = stock["S33Nm"].iloc[-1] if "S33Nm" in stock.columns else ""
        ok = True

        if use_ma:
            mas = close.rolling(int(ma_short)).mean()
            mal = close.rolling(int(ma_long)).mean()
            if not (mas.iloc[-2] <= mal.iloc[-2] and mas.iloc[-1] > mal.iloc[-1]):
                ok = False

        if use_rsi and ok:
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(int(rsi_period)).mean()
            loss = (-delta.clip(upper=0)).rolling(int(rsi_period)).mean()
            rsi = 100 - (100 / (1 + gain / loss))
            val = rsi.iloc[-1]
            if pd.isna(val) or not (rsi_min <= val <= rsi_max):
                ok = False

        if use_stoch and ok:
            lmin = low.rolling(int(stoch_k)).min()
            hmax = high.rolling(int(stoch_k)).max()
            k = 100 * (close - lmin) / (hmax - lmin)
            d = k.rolling(int(stoch_d)).mean()
            kv = k.iloc[-1]
            dv = d.iloc[-1]
            if pd.isna(kv) or pd.isna(dv):
                ok = False
            elif not (stoch_min <= kv <= stoch_max):
                ok = False
            elif use_stoch_gc:
                if not (k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] > d.iloc[-1]):
                    ok = False

        if use_bb and ok:
            mid = close.rolling(int(bb_period)).mean()
            std = close.rolling(int(bb_period)).std()
            lower = mid - bb_sigma * std
            if close.iloc[-1] >= lower.iloc[-1]:
                ok = False

        if ok:
            results.append({
                "コード": code,
                "銘柄名": name,
                "業種": sector,
                "終値": close.iloc[-1],
                "日付": stock["Date"].iloc[-1].strftime("%Y-%m-%d")
            })

        progress.progress((i + 1) / len(codes))

    st.subheader(f"結果: {len(results)}銘柄")

    if results:
        result_df = pd.DataFrame(results)
        st.dataframe(result_df)

        sel = st.selectbox("チャートを見る銘柄", result_df["コード"].tolist())
        if sel:
            s = df[df["Code"] == sel].sort_values("Date")
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(s["Date"], s["C"], label="終値")
            ax.set_title(str(sel))
            ax.legend()
            st.pyplot(fig)

        csv = result_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("CSVダウンロード", csv, "results.csv", "text/csv")
    else:
        st.warning("条件に一致する銘柄がありませんでした")