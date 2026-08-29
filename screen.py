# screen.py - 完全ローカル版（API通信なし）
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import glob

st.set_page_config(page_title="株式スクリーニング", layout="wide")
st.title("📈 株式スクリーニングシステム（ローカル版）")

# ===== CSS =====
st.markdown("""
<style>
div[data-testid="column"]:last-child .stButton button {
    font-size: 11px !important;
    padding: 2px 6px !important;
    height: 26px !important;
}
</style>
""", unsafe_allow_html=True)

# ===== CSVファイル選択 =====
csv_files = glob.glob("C:/stock_system/*.csv")
if not csv_files:
    st.error("❌ CSVファイルが見つかりません")
    st.stop()

selected_csv = st.sidebar.selectbox(
    "📂 データファイル選択",
    csv_files,
    format_func=lambda x: Path(x).name
)

# ===== データ読み込み（キャッシュ付き） =====
@st.cache_data
def load_data(filepath):
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()

    # カラム名統一
    col_map = {
        'C': 'Close', 'O': 'Open', 'H': 'High', 'L': 'Low',
        'CoName': 'Name', 'S33Nm': 'Sector',
        'Code': 'Code', 'Date': 'Date'
    }
    df = df.rename(columns=col_map)

    df['Date'] = pd.to_datetime(df['Date'])
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df['Open']  = pd.to_numeric(df['Open'],  errors='coerce')
    df['High']  = pd.to_numeric(df['High'],  errors='coerce')
    df['Low']   = pd.to_numeric(df['Low'],   errors='coerce')
    df['Code']  = df['Code'].astype(str)

    # 銘柄名・業種がなければ空欄
    if 'Name'   not in df.columns: df['Name']   = '不明'
    if 'Sector' not in df.columns: df['Sector'] = '不明'

    return df

with st.spinner("📊 データ読み込み中..."):
    df_all = load_data(selected_csv)

st.sidebar.success(f"✅ {len(df_all):,}行 読み込み完了")

# ===== 日付範囲 =====
min_date = df_all['Date'].min().date()
max_date = df_all['Date'].max().date()
st.sidebar.markdown(f"📅 データ期間: `{min_date}` ～ `{max_date}`")

# ===== スクリーニング条件 =====
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 スクリーニング条件")

# 移動平均
use_ma = st.sidebar.checkbox("📊 移動平均クロス", value=True)
if use_ma:
    ma_short = st.sidebar.slider("短期MA", 5, 30, 5)
    ma_long  = st.sidebar.slider("長期MA", 10, 120, 25)

# RSI
use_rsi = st.sidebar.checkbox("📉 RSI", value=False)
if use_rsi:
    rsi_period = st.sidebar.slider("RSI期間", 5, 30, 14)
    rsi_min    = st.sidebar.slider("RSI下限", 0, 50, 30)
    rsi_max    = st.sidebar.slider("RSI上限", 50, 100, 70)

# ストキャスティクス
use_stoch = st.sidebar.checkbox("🎯 ストキャスティクス", value=False)
if use_stoch:
    stoch_k    = st.sidebar.slider("%K期間", 5, 30, 14)
    stoch_d    = st.sidebar.slider("%D期間", 3, 10, 3)
    stoch_min  = st.sidebar.slider("買いゾーン上限(%)", 10, 50, 20)
    golden_cross = st.sidebar.checkbox("%Kが%Dをゴールデンクロス", value=True)

# ボリュームフィルタ
use_vol = st.sidebar.checkbox("📦 出来高フィルタ", value=False)
if use_vol:
    vol_min = st.sidebar.number_input("最低出来高", value=100000, step=10000)

# 業種フィルタ
sectors = ['すべて'] + sorted(df_all['Sector'].dropna().unique().tolist())
selected_sector = st.sidebar.selectbox("🏭 業種フィルタ", sectors)

# ===== スクリーニング実行 =====
col_run, col_clear = st.columns([1, 1])
run_btn   = col_run.button("🚀 スクリーニング実行", use_container_width=True)
clear_btn = col_clear.button("🗑️ 結果クリア", use_container_width=True)

if clear_btn:
    st.session_state.pop('results', None)

if run_btn:
    results = []
    codes = df_all['Code'].unique()
    progress = st.progress(0)
    status   = st.empty()

    for i, code in enumerate(codes):
        df = df_all[df_all['Code'] == code].sort_values('Date').copy()

        if len(df) < 30:
            continue

        # 業種フィルタ
        if selected_sector != 'すべて':
            if df['Sector'].iloc[-1] != selected_sector:
                continue

        passed = True
        reason = {}

        # --- 移動平均 ---
        if use_ma:
            df['MA_S'] = df['Close'].rolling(ma_short).mean()
            df['MA_L'] = df['Close'].rolling(ma_long).mean()
            if df['MA_S'].isna().iloc[-1] or df['MA_L'].isna().iloc[-1]:
                passed = False
            else:
                cross = (df['MA_S'].iloc[-2] <= df['MA_L'].iloc[-2]) and \
                        (df['MA_S'].iloc[-1]  >  df['MA_L'].iloc[-1])
                if not cross:
                    passed = False
                else:
                    reason['MA'] = f"MA{ma_short}↑MA{ma_long}"

        # --- RSI ---
        if passed and use_rsi:
            delta = df['Close'].diff()
            gain  = delta.clip(lower=0).rolling(rsi_period).mean()
            loss  = (-delta.clip(upper=0)).rolling(rsi_period).mean()
            rs    = gain / loss.replace(0, np.nan)
            rsi   = 100 - (100 / (1 + rs))
            val   = rsi.iloc[-1]
            if np.isnan(val) or not (rsi_min <= val <= rsi_max):
                passed = False
            else:
                reason['RSI'] = f"RSI={val:.1f}"

        # --- ストキャスティクス ---
        if passed and use_stoch:
            low_k  = df['Low'].rolling(stoch_k).min()
            high_k = df['High'].rolling(stoch_k).max()
            k_line = 100 * (df['Close'] - low_k) / (high_k - low_k).replace(0, np.nan)
            d_line = k_line.rolling(stoch_d).mean()

            k_now  = k_line.iloc[-1]
            d_now  = d_line.iloc[-1]
            k_prev = k_line.iloc[-2]
            d_prev = d_line.iloc[-2]

            if any(np.isnan(v) for v in [k_now, d_now, k_prev, d_prev]):
                passed = False
            else:
                in_zone = k_now <= stoch_min
                if golden_cross:
                    cross = (k_prev <= d_prev) and (k_now > d_now)
                    if not (in_zone and cross):
                        passed = False
                    else:
                        reason['Stoch'] = f"%K={k_now:.1f} %D={d_now:.1f} GC"
                else:
                    if not in_zone:
                        passed = False
                    else:
                        reason['Stoch'] = f"%K={k_now:.1f} %D={d_now:.1f}"

        # --- 出来高 ---
        if passed and use_vol:
            if 'Volume' in df.columns:
                if df['Volume'].iloc[-1] < vol_min:
                    passed = False
            # Volumeカラムがなければスキップ

        if passed:
            results.append({
                'Code'  : code,
                'Name'  : df['Name'].iloc[-1],
                'Sector': df['Sector'].iloc[-1],
                'Close' : df['Close'].iloc[-1],
                'Date'  : df['Date'].iloc[-1].strftime('%Y-%m-%d'),
                'Signal': ' / '.join(reason.values()),
            })

        progress.progress((i + 1) / len(codes))
        if i % 100 == 0:
            status.text(f"処理中: {i}/{len(codes)} 銘柄...")

    progress.empty()
    status.empty()
    st.session_state['results'] = results

# ===== 結果表示 =====
if 'results' in st.session_state:
    results = st.session_state['results']

    if not results:
        st.warning("⚠️ 条件に合う銘柄が見つかりませんでした")
    else:
        st.success(f"✅ {len(results)} 銘柄がヒットしました")
        df_res = pd.DataFrame(results)

        # ヘッダー
        hcols = st.columns([0.4, 1.2, 2.5, 2, 1.5, 1.8, 1.5, 0.5])
        for h, label in zip(hcols, ['#','コード','銘柄名','業種','終値','日付','シグナル','📈']):
            h.markdown(f"**{label}**")
        st.markdown("---")

        # データ行
        for i, row in df_res.iterrows():
            cols = st.columns([0.4, 1.2, 2.5, 2, 1.5, 1.8, 1.5, 0.5])
            cols[0].write(i + 1)
            cols[1].write(row['Code'])
            cols[2].write(row['Name'])
            cols[3].write(row['Sector'])
            cols[4].write(f"¥{row['Close']:,.1f}")
            cols[5].write(row['Date'])
            cols[6].write(row['Signal'])

            if cols[7].button("📈", key=f"chart_{i}"):
                st.session_state['chart_code'] = row['Code']

        # ダウンロード
        csv_dl = df_res.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("💾 CSVダウンロード", csv_dl, "screening_result.csv", "text/csv")

# ===== チャート表示 =====
if 'chart_code' in st.session_state:
    code = st.session_state['chart_code']
    df_c = df_all[df_all['Code'] == code].sort_values('Date').copy()
    name = df_c['Name'].iloc[-1] if 'Name' in df_c.columns else code

    st.markdown(f"---\n### 📊 {code} {name} チャート")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_c['Date'], open=df_c['Open'], high=df_c['High'],
        low=df_c['Low'], close=df_c['Close'], name='ローソク足'
    ))

    if use_ma:
        df_c['MA_S'] = df_c['Close'].rolling(ma_short).mean()
        df_c['MA_L'] = df_c['Close'].rolling(ma_long).mean()
        fig.add_trace(go.Scatter(x=df_c['Date'], y=df_c['MA_S'],
                                  name=f'MA{ma_short}', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=df_c['Date'], y=df_c['MA_L'],
                                  name=f'MA{ma_long}', line=dict(color='blue')))

    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    if st.button("❌ チャートを閉じる"):
        del st.session_state['chart_code']
        st.rerun()