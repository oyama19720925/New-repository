import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ========== ページ設定 ==========
st.set_page_config(page_title="株スクリーニング", layout="wide")
st.title("📈 株スクリーニングシスチE")

# ========== CSVファイル検E ==========
csv_files = glob.glob("*.csv")
if not csv_files:
    st.error("❌ CSVファイルが見つかりません。stock_systemフォルダにCSVを置いてください。")
    st.stop()

    selected_csv = st.sidebar.selectbox("📂 CSVファイルを選択", csv_files)

# ========== データ読み込み ==========
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype={'Code': str})
    df['Date'] = pd.to_datetime(df['Date'])
    
    # ☁ECoName がなければ stock_master.csv からマEジ
    if 'CoName' not in df.columns:
        master_path = os.path.join(os.path.dirname(os.path.abspath(path)), 'stock_master.csv')
        if os.path.exists(master_path):
            master = pd.read_csv(master_path, dtype={'Code': str})
            cols = ['Code']
            for c in ['CoName', 'S33Nm', 'MktNm']:
                if c in master.columns:
                    cols.append(c)
            df = df.merge(master[cols], on='Code', how='left')
    
    # ☁EVo がなければ 0 で埋めめE
    if 'Vo' not in df.columns:
        df['Vo'] = 0
    
    return df

df_all = load_data(selected_csv)

# ========== 列名定義 ==========
COL_DATE   = 'Date'
COL_CODE   = 'Code'
COL_NAME   = 'CoName'
COL_SECTOR = 'S33Nm'
COL_MARKET = 'MktNm'
COL_OPEN   = 'O'
COL_HIGH   = 'H'
COL_LOW    = 'L'
COL_CLOSE  = 'C'
COL_VOLUME = 'Vo'

# ========== 列名チェチE ==========
required_cols = [COL_DATE, COL_CODE, COL_NAME, COL_OPEN, COL_HIGH, COL_LOW, COL_CLOSE, COL_VOLUME]
missing_cols = [c for c in required_cols if c not in df_all.columns]
if missing_cols:
    st.error(f"❌ 必要な列が見つかりません: {missing_cols}")
    st.write("📋 実際の列名:", df_all.columns.tolist())
    st.stop()

# ========== サイドバーEフィルタ ==========
st.sidebar.header("🔧 フィルタ設定")

# --- 期間 ---
st.sidebar.subheader("📅 期間")
date_min = df_all[COL_DATE].min().date()
date_max = df_all[COL_DATE].max().date()
start_date = st.sidebar.date_input("開始日", value=date_min, min_value=date_min, max_value=date_max)
end_date   = st.sidebar.date_input("終亁E", value=date_max, min_value=date_min, max_value=date_max)

# --- 市場 ---
st.sidebar.subheader("🏢 市場")
if COL_MARKET in df_all.columns:
    markets = sorted(df_all[COL_MARKET].dropna().unique().tolist())
    selected_markets = st.sidebar.multiselect("市場を選択（未選択=全て）", markets)
else:
    selected_markets = []

# --- 業種 ---
st.sidebar.subheader("🏭 業種")
if COL_SECTOR in df_all.columns:
    sectors = sorted(df_all[COL_SECTOR].dropna().unique().tolist())
    selected_sectors = st.sidebar.multiselect("業種を選択（未選択=全て）", sectors)
else:
    selected_sectors = []

# ========== サイドバー分析ツール ==========
st.sidebar.header("📊 フィルタ＆ツール")

# --- 移動平均 ---
st.sidebar.subheader("📉 移動平均")
use_ma = st.sidebar.checkbox("移動平均を使用", value=True)
if use_ma:
    ma_short = st.sidebar.number_input("短期MA（日）", min_value=1, max_value=200, value=5)
    ma_long  = st.sidebar.number_input("長期MA（日）", min_value=1, max_value=200, value=25)
    ma_cond  = st.sidebar.selectbox("条件", ['ゴールデンクロス', '短期MA > 長期MA', '短期MA < 長期MA'])
else:
    ma_short = 5
    ma_long  = 25
    ma_cond  = 'ゴールデンクロス'

# --- RSI ---
st.sidebar.subheader("📊 RSI")
use_rsi = st.sidebar.checkbox("RSIを使用", value=False)
if use_rsi:
    rsi_period = st.sidebar.number_input("RSI期間（日）", min_value=2, max_value=100, value=14)
    rsi_min    = st.sidebar.slider("RSI 最小値", 0, 100, 30)
    rsi_max    = st.sidebar.slider("RSI 最大値", 0, 100, 70)
else:
    rsi_period = 14
    rsi_min    = 30
    rsi_max    = 70

# --- ストキャスティクス ---
st.sidebar.subheader("📈 ストキャスティクス")
use_stoch = st.sidebar.checkbox("ストキャスティクスを使用", value=False)
if use_stoch:
    stoch_k   = st.sidebar.number_input("%K期間（日）", min_value=1, max_value=100, value=14)
    stoch_d   = st.sidebar.number_input("%D期間（日）", min_value=1, max_value=100, value=3)
    stoch_cond = st.sidebar.selectbox("条件", ['ゴールデンクロス', '%K > %D', '%K < %D'])
    stoch_pos_filter = st.sidebar.checkbox("%K の篁Eでフィルタ", value=False)
    if stoch_pos_filter:
        stoch_pos_min = st.sidebar.slider("%K 最小値", 0, 100, 20)
        stoch_pos_max = st.sidebar.slider("%K 最大値", 0, 100, 80)
    else:
        stoch_pos_min = 0
        stoch_pos_max = 100
else:
    stoch_k   = 14
    stoch_d   = 3
    stoch_cond = 'ゴールデンクロス'
    stoch_pos_filter = False
    stoch_pos_min = 0
    stoch_pos_max = 100

# --- 出来高---
st.sidebar.subheader("📦 出来高")
use_volume = st.sidebar.checkbox("出来高を使用", value=False)
if use_volume:
    vol_days = st.sidebar.number_input("平均日数", min_value=1, max_value=60, value=5)
    vol_min  = st.sidebar.number_input("最小出来高（平均）", min_value=0, value=100000, step=10000)
else:
    vol_days = 5
    vol_min  = 100000

# ========== データ絞り込み ==========
target_df = df_all[
    (df_all[COL_DATE] >= pd.Timestamp(start_date)) &
    (df_all[COL_DATE] <= pd.Timestamp(end_date))
].copy()

if selected_markets:
    target_df = target_df[target_df[COL_MARKET].isin(selected_markets)]

if selected_sectors:
    target_df = target_df[target_df[COL_SECTOR].isin(selected_sectors)]

st.write(f"📋 対象データ: {len(target_df):,} 行 / {target_df[COL_CODE].nunique():,} 銘柄")

# ========== スクリーニング関数 ==========
def do_screening(df):
    results = []

    for code, group in df.groupby(COL_CODE):
        group = group.sort_values(COL_DATE).reset_index(drop=True)

        if len(group) < 2:
            continue

        last = group.iloc[-1]

        # 銘柄名を安Eに取征E
        name = last[COL_NAME] if COL_NAME in group.columns else ''

        close  = group[COL_CLOSE].values.astype(float)
        high   = group[COL_HIGH].values.astype(float)
        low    = group[COL_LOW].values.astype(float)
        volume = group[COL_VOLUME].values.astype(float)

        passed = True

        # ========== 移動平均 ==========
        if use_ma:
            if len(close) < ma_long:
                continue
            ma_s = pd.Series(close).rolling(ma_short).mean()
            ma_l = pd.Series(close).rolling(ma_long).mean()
            if pd.isna(ma_s.iloc[-1]) or pd.isna(ma_l.iloc[-1]):
                continue
            if len(ma_s) < 2 or len(ma_l) < 2:
                continue
            if ma_cond == 'ゴールデンクロス':
                if not (ma_s.iloc[-2] < ma_l.iloc[-2] and ma_s.iloc[-1] > ma_l.iloc[-1]):
                    passed = False
            elif ma_cond == '短期MA > 長期MA':
                if not (ma_s.iloc[-1] > ma_l.iloc[-1]):
                    passed = False
            elif ma_cond == '短期MA < 長期MA':
                if not (ma_s.iloc[-1] < ma_l.iloc[-1]):
                    passed = False

        # ========== RSI ==========
        if use_rsi:
            if len(close) < rsi_period + 1:
                continue
            delta = pd.Series(close).diff()
            gain  = delta.clip(lower=0).rolling(rsi_period).mean()
            loss  = (-delta.clip(upper=0)).rolling(rsi_period).mean()
            rs    = gain / loss
            rsi   = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            if pd.isna(rsi_val):
                continue
            if not (rsi_min <= rsi_val <= rsi_max):
                passed = False

        # ========== ストキャスティクス ==========
        if use_stoch:
            need = stoch_k + stoch_d - 1
            if len(close) < need:
                continue
            lo_k  = pd.Series(low).rolling(stoch_k).min()
            hi_k  = pd.Series(high).rolling(stoch_k).max()
            denom = hi_k - lo_k
            denom = denom.replace(0, float('nan'))
            pct_k = 100 * (pd.Series(close) - lo_k) / denom
            pct_d = pct_k.rolling(stoch_d).mean()

            k_val = pct_k.iloc[-1]
            d_val = pct_d.iloc[-1]

            if pd.isna(k_val) or pd.isna(d_val):
                continue

            if stoch_cond == 'ゴールデンクロス':
                if len(pct_k) < 2 or len(pct_d) < 2:
                    continue
                if not (pct_k.iloc[-2] < pct_d.iloc[-2] and k_val > d_val):
                    passed = False
            elif stoch_cond == '%K > %D':
                if not (k_val > d_val):
                    passed = False
            elif stoch_cond == '%K < %D':
                if not (k_val < d_val):
                    passed = False

            if stoch_pos_filter:
                if not (stoch_pos_min <= k_val <= stoch_pos_max):
                    passed = False

        # ========== 出来高==========
        if use_volume:
            if len(volume) < vol_days:
                continue
            vol_avg = pd.Series(volume).rolling(vol_days).mean().iloc[-1]
            if pd.isna(vol_avg):
                continue
            if not (vol_avg >= vol_min):
                passed = False

        if passed:
            results.append({
                '銘柄コード': code,
                '銘柄名':     name,
                '終値':       last[COL_CLOSE],
                '日付':       last[COL_DATE],
            })

    return pd.DataFrame(results)

# ========== 実行ボタン ==========
col1, col2 = st.columns(2)

with col1:
    run_btn = st.button("🔍 スクリーニング実行", type="primary", use_container_width=True)

with col2:
    run_all_btn = st.button("📋 全銘柄表示（条件なし）", use_container_width=True)

# ========== スクリーニング実行==========
if run_btn:
    if not use_ma and not use_rsi and not use_stoch and not use_volume:
        st.warning("⚠️ フィルタが全てOFFです。少なくとも1つをONにしてください。")
    else:
        with st.spinner("⏳ スクリーニング中..."):
            result_df = do_screening(target_df)

        if result_df.empty:
            st.warning("⚠️ 条件に合う銘柄が見つかりませんでした。条件を緩めてみてください。")
        else:
            st.success(f"✅ {len(result_df)} 銘柄が条件に一致しました！")
            st.dataframe(result_df, use_container_width=True)

            # ダウンロード
            csv_out = result_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 結果をCSVダウンロード,
                data=csv_out,
                file_name="screening_result.csv",
                mime="text/csv"
            )

# ========== 全銘柄表示 ==========
if run_all_btn:
    with st.spinner("⏳ 雁E中..."):
        summary_list = []
        for code, group in target_df.groupby(COL_CODE):
            group = group.sort_values(COL_DATE).reset_index(drop=True)
            last = group.iloc[-1]
            name = last[COL_NAME] if COL_NAME in group.columns else ''
            summary_list.append({
                '銘柄コード': code,
                '銘柄名':     name,
                '終値':       last[COL_CLOSE],
                '日付':       last[COL_DATE],
            })
        summary_df = pd.DataFrame(summary_list)

    st.success(f"📋 全 {len(summary_df)} 銘柄")
    st.dataframe(summary_df, use_container_width=True)

    csv_out = summary_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="💾 全銘柄CSVダウンロード,
        data=csv_out,
        file_name="all_stocks.csv",
        mime="text/csv"
    )

# ========== チャート表示 ==========
st.header("📊 個別チャート")
chart_code = st.text_input("銘柄コードを入力（例: 7203）", value="")

if chart_code:
    chart_df = df_all[df_all[COL_CODE] == chart_code].sort_values(COL_DATE).reset_index(drop=True)

    if chart_df.empty:
        st.warning(f"⚠️ 銘柄コード {chart_code} のデータが見つかりません。")
    else:
        name_val = chart_df.iloc[-1][COL_NAME] if COL_NAME in chart_df.columns else ''
        st.subheader(f"{chart_code}  {name_val}")

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.6, 0.2, 0.2],
            vertical_spacing=0.05,
            subplot_titles=("ローソク足 + MA", "出来高, "RSI / ストキャスティクス")
        )

        # ローソク足
        fig.add_trace(go.Candlestick(
            x=chart_df[COL_DATE],
            open=chart_df[COL_OPEN],
            high=chart_df[COL_HIGH],
            low=chart_df[COL_LOW],
            close=chart_df[COL_CLOSE],
            name="ローソク足"
        ), row=1, col=1)

        # 移動平均線
        for period, color in [(5, 'blue'), (25, 'orange'), (75, 'green')]:
            ma = chart_df[COL_CLOSE].rolling(period).mean()
            fig.add_trace(go.Scatter(
                x=chart_df[COL_DATE], y=ma,
                name=f"MA{period}", line=dict(color=color, width=1)
            ), row=1, col=1)

        # 出来高
        fig.add_trace(go.Bar(
            x=chart_df[COL_DATE],
            y=chart_df[COL_VOLUME],
            name="出来高,
            marker_color='lightblue'
        ), row=2, col=1)

        # RSI
        delta   = chart_df[COL_CLOSE].diff()
        gain    = delta.clip(lower=0).rolling(14).mean()
        loss    = (-delta.clip(upper=0)).rolling(14).mean()
        rs      = gain / loss
        rsi_line = 100 - (100 / (1 + rs))
        fig.add_trace(go.Scatter(
            x=chart_df[COL_DATE], y=rsi_line,
            name="RSI(14)", line=dict(color='purple', width=1)
        ), row=3, col=1)

        # ストキャスティクス
        lo14  = chart_df[COL_LOW].rolling(14).min()
        hi14  = chart_df[COL_HIGH].rolling(14).max()
        denom = (hi14 - lo14).replace(0, float('nan'))
        k_line = 100 * (chart_df[COL_CLOSE] - lo14) / denom
        d_line = k_line.rolling(3).mean()
        fig.add_trace(go.Scatter(
            x=chart_df[COL_DATE], y=k_line,
            name="%K", line=dict(color='red', width=1)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=chart_df[COL_DATE], y=d_line,
            name="%D", line=dict(color='blue', width=1, dash='dash')
        ), row=3, col=1)

        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)
