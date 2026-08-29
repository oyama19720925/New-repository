# fix_click.py - app.pyにクリック選択チャート機能を追加

new_app = '''# app.py - 株式スクリーニングシステム
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import os

# =============================
# ページ設定
# =============================
st.set_page_config(
    page_title="株式スクリーニングシステム",
    page_icon="📈",
    layout="wide"
)

st.title("📈 株式スクリーニングシステム")

# =============================
# CSVファイル検索
# =============================
csv_files = sorted(set(glob.glob('stocks_OHLC_*.csv')))
if not csv_files:
    st.error("❌ OHLCのCSVファイルが見つかりません")
    st.stop()

selected_csv = st.sidebar.selectbox("📂 データファイル選択", sorted(csv_files, reverse=True))

# =============================
# データ読み込み
# =============================
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding='utf-8')
    # 列名の正規化
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ['code','銘柄コード','ticker']: col_map[c] = 'Code'
        elif cl in ['name','銘柄名','company']: col_map[c] = 'Name'
        elif cl in ['date','日付','取引日']: col_map[c] = 'Date'
        elif cl in ['open','始値']: col_map[c] = 'Open'
        elif cl in ['high','高値']: col_map[c] = 'High'
        elif cl in ['low','安値']: col_map[c] = 'Low'
        elif cl in ['close','終値']: col_map[c] = 'Close'
        elif cl in ['volume','出来高']: col_map[c] = 'Volume'
    df = df.rename(columns=col_map)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Code'] = df['Code'].astype(str)
    return df

df_all = load_data(selected_csv)

# 銘柄名辞書
name_dict = {}
if 'Name' in df_all.columns:
    name_dict = df_all.drop_duplicates('Code').set_index('Code')['Name'].to_dict()

# =============================
# サイドバー：スクリーニング条件
# =============================
st.sidebar.markdown("---")
st.sidebar.header("🔍 スクリーニング条件")

# 移動平均
use_ma = st.sidebar.checkbox("移動平均ゴールデンクロス", value=True)
ma_short = st.sidebar.number_input("短期MA", value=5, min_value=1)
ma_long  = st.sidebar.number_input("長期MA", value=25, min_value=2)

# RSI
use_rsi = st.sidebar.checkbox("RSI条件", value=False)
rsi_period = st.sidebar.number_input("RSI期間", value=14, min_value=2)
rsi_min = st.sidebar.number_input("RSI下限", value=30, min_value=0)
rsi_max = st.sidebar.number_input("RSI上限", value=70, min_value=0)

# ストキャスティクス
use_stoch = st.sidebar.checkbox("ストキャスティクス", value=False)
stoch_k = st.sidebar.number_input("%K期間", value=14, min_value=1)
stoch_d = st.sidebar.number_input("%D期間", value=3,  min_value=1)
stoch_min = st.sidebar.number_input("ストキャス下限(%)", value=20, min_value=0)
stoch_max = st.sidebar.number_input("ストキャス上限(%)", value=80, min_value=0)
use_stoch_gc = st.sidebar.checkbox("ストキャスGC検出", value=False)

# ボリンジャーバンド
use_bb = st.sidebar.checkbox("ボリンジャーバンド", value=False)
bb_period = st.sidebar.number_input("BB期間", value=20, min_value=2)
bb_sigma  = st.sidebar.number_input("BB sigma", value=2.0, min_value=0.1)

# 出来高
use_vol = st.sidebar.checkbox("出来高急増", value=False)
vol_ratio = st.sidebar.number_input("出来高倍率", value=2.0, min_value=1.0)

run_btn = st.sidebar.button("🚀 スクリーニング実行")

# =============================
# インジケーター計算
# =============================
def calc_indicators(df):
    df = df.sort_values('Date').copy()
    df['MA_short'] = df['Close'].rolling(int(ma_short)).mean()
    df['MA_long']  = df['Close'].rolling(int(ma_long)).mean()
    # RSI
    delta = df['Close'].diff()
    gain  = delta.clip(lower=0).rolling(int