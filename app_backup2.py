import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="株スクリーニング", layout="wide")
st.title("📈 株式スクリーニングシステム")

# ============================================================
# CSVファイル選択
# ============================================================
csv_files = glob.glob("*.csv")
if not csv_files:
    st.error("CSVファイルが見つかりません")
    st.stop()

selected_file = st.sidebar.selectbox("📂 CSVファイル選択", csv_files)

@st.cache_data
def load_data(filepath):
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    # 列名を標準化
    rename_map = {}
    for col in df.columns:
        if col in ['O', 'open']:
            rename_map[col] = 'Open'
        elif col in ['H', 'high']:
            rename_map[col] = 'High'
        elif col in ['L', 'low']:
            rename_map[col] = 'Low'
        elif col in ['C', 'close']:
            rename_map[col] = 'Close'
        elif col in ['V', 'volume', 'Volume']:
            rename_map[col] = 'Volume'
        elif col in ['code', 'CODE']:
            rename_map[col] = 'Code'
        elif col in ['date', 'DATE']:
            rename_map[col] = 'Date'
    df = df.rename(columns=rename_map)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Code'] = df['Code'].astype(str)
    df = df.sort_values(['Code', 'Date']).reset_index(drop=True)
    return df

# ============================================================
# 銘柄名マスタ（なければコードのみ）
# ============================================================
@st.cache_data
def load_master():
    master_files = glob.glob("*master*.csv") + glob.glob("*銘柄*.csv") + glob.glob("*name*.csv")
    if master_files:
        m = pd.read_csv(master_files[0], encoding='utf-8-sig')
        m.columns = m.columns.str.strip()
        m['Code'] = m['Code'].astype(str) if 'Code' in m.columns else m.iloc[:,0].astype(str)
        return m
    return None

with st.spinner("データ読み込み中..."):
    df_all = load_data(selected_file)
    master_df = load_master()

st.success(f"✅ {len(df_all):,} 行 / {df_all['Code'].nunique():,} 銘柄 読み込み完了")

# ============================================================
# サイドバー：分析ツール ON/OFF
# ============================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 分析ツール設定")

use_ma    = st.sidebar.checkbox("移動平均線 (MA)", value=True)
use_stoch = st.sidebar.checkbox("ストキャスティクス", value=False)
use_vol   = st.sidebar.checkbox("出来高フィルター", value=False)

# ============================================================
# 移動平均パラメータ
# ============================================================
if use_ma:
    st.sidebar.markdown("#### 📊 移動平均線")
    ma_short = st.sidebar.number_input("短期MA", min_value=1, max_value=100, value=5)
    ma_long  = st.sidebar.number_input("長期MA", min_value=1, max_value=300, value=25)
    ma_cond  = st.sidebar.selectbox("条件", ["短期 > 長期（上昇）", "短期 < 長期（下降）", "ゴールデンクロス"])

# ============================================================
# ストキャスティクスパラメータ
# ============================================================
if use_stoch:
    st.sidebar.markdown("#### 📉 ストキャスティクス")
    stoch_k     = st.sidebar.number_input("%K 期間", min_value=1, max_value=100, value=14)
    stoch_d     = st.sidebar.number_input("%D 期間", min_value=1, max_value=100, value=3)
    stoch_cond  = st.sidebar.selectbox("条件", [
        "%K が %D を上抜け（ゴールデンクロス）",
        "%K が %D を下抜け（デッドクロス）",
        "%K < 20（売られすぎ）",
        "%K > 80（買われすぎ）",
    ])

# ============================================================
# 出来高パラメータ
# ============================================================
if use_vol:
    st.sidebar.markdown("#### 📦 出来高")
    vol_period = st.sidebar.number_input("平均期間（日）", min_value=1, max_value=100, value=25)
    vol_ratio  = st.sidebar.number_input("倍率（直近/平均）", min_value=0.1, max_value=10.0, value=1.5, step=0.1)

st.sidebar.markdown("---")
run_btn = st.sidebar.button("🔍 スクリーニング実行", use_container_width=True)

# ============================================================
# 計算関数
# ============================================================
def calc_ma(group, short, long):
    group = group.copy()
    group[f"MA{short}"] = group["Close"].rolling(short).mean()
    group[f"MA{long}"]  = group["Close"].rolling(long).mean()
    return group

def calc_stoch(group, k_period, d_period):
    group = group.copy()
    low_min  = group["Low"].rolling(k_period).min()
    high_max = group["High"].rolling(k_period).max()
    denom = high_max - low_min
    group["%K"] = np.where(denom == 0, 50.0, (group["Close"] - low_min) / denom * 100)
    group["%D"] = group["%K"].rolling(d_period).mean()
    return group

def calc_vol(group, period):
    group = group.copy()
    if "Volume" in group.columns:
        group["Vol_MA"] = group["Volume"].rolling(period).mean()
    return group

# ============================================================
# スクリーニング本体
# ============================================================
def run_screening(df):
    results = []
    codes = df['Code'].unique()

    for code in codes:
        g = df[df['Code'] == code].copy().reset_index(drop=True)

        if len(g) < 2:
            continue

        # --- 移動平均 ---
        if use_ma:
            need = max(ma_short, ma_long)
            if len(g) < need:
                continue
            g = calc_ma(g, ma_short, ma_long)
            last  = g.iloc[-1]
            prev  = g.iloc[-2]
            ms, ml = f"MA{ma_short}", f"MA{ma_long}"
            if pd.isna(last[ms]) or pd.isna(last[ml]):
                continue
            if ma_cond == "短期 > 長期（上昇）":
                if not (last[ms] > last[ml]):
                    continue
            elif ma_cond == "短期 < 長期（下降）":
                if not (last[ms] < last[ml]):
                    continue
            elif ma_cond == "ゴールデンクロス":
                if pd.isna(prev[ms]) or pd.isna(prev[ml]):
                    continue
                if not (prev[ms] <= prev[ml] and last[ms] > last[ml]):
                    continue

        # --- ストキャスティクス ---
        if use_stoch:
            need = stoch_k + stoch_d
            if len(g) < need:
                continue
            g = calc_stoch(g, stoch_k, stoch_d)
            last = g.iloc[-1]
            prev = g.iloc[-2]
            if pd.isna(last["%K"]) or pd.isna(last["%D"]):
                continue
            if stoch_cond == "%K が %D を上抜け（ゴールデンクロス）":
                if pd.isna(prev["%K"]) or pd.isna(prev["%D"]):
                    continue
                if not (prev["%K"] <= prev["%D"] and last["%K"] > last["%D"]):
                    continue
            elif stoch_cond == "%K が %D を下抜け（デッドクロス）":
                if pd.isna(prev["%K"]) or pd.isna(prev["%D"]):
                    continue
                if not (prev["%K"] >= prev["%D"] and last["%K"] < last["%D"]):
                    continue
            elif stoch_cond == "%K < 20（売られすぎ）":
                if not (last["%K"] < 20):
                    continue
            elif stoch_cond == "%K > 80（買われすぎ）":
                if not (last["%K"] > 80):
                    continue

        # --- 出来高 ---
        if use_vol:
            if "Volume" not in g.columns:
                continue
            if len(g) < vol_period:
                continue
            g = calc_vol(g, vol_period)
            last = g.iloc[-1]
            if pd.isna(last["Vol_MA"]) or last["Vol_MA"] == 0:
                continue
            if not (last["Volume"] >= last["Vol_MA"] * vol_ratio):
                continue

        last_row = g.iloc[-1]
        results.append({
            "Code":       code,
            "日付":        last_row["Date"].strftime("%Y-%m-%d"),
            "終値":        last_row["Close"],
            "MA短期":      round(last_row[f"MA{ma_short}"], 2) if use_ma else "-",
            "MA長期":      round(last_row[f"MA{ma_long}"], 2)  if use_ma else "-",
            "%K":         round(last_row["%K"], 2) if use_stoch else "-",
            "%D":         round(last_row["%D"], 2) if use_stoch else "-",
        })

    return pd.DataFrame(results)

# ============================================================
# 実行・表示
# ============================================================
if run_btn:
   import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
rcParams['font.family'] = 'MS Gothic'

st.set_page_config(page_title="株スクリーニング", layout="wide")
st.title("📈 株式スクリーニングシステム")

# ========== CSVファイル選択 ==========
csv_files = glob.glob("*.csv")
if not csv_files:
    st.error("CSVファイルが見つかりません")
    st.stop()

selected_file = st.sidebar.selectbox("📂 CSVファイルを選択", csv_files)

@st.cache_data
def load_data(filepath):
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    df['Date'] = pd.to_datetime(df['Date'])
    # 列名を統一
    rename_map = {}
    for col in df.columns:
        if col == 'O': rename_map[col] = 'Open'
        elif col == 'H': rename_map[col] = 'High'
        elif col == 'L': rename_map[col] = 'Low'
        elif col == 'C': rename_map[col] = 'Close'
        elif col == 'V': rename_map[col] = 'Volume'
    df = df.rename(columns=rename_map)
    return df

df_all = load_data(selected_file)
st.sidebar.success(f"✅ {len(df_all)}行 読み込み完了")

# 銘柄名列の確認
has_name = 'Name' in df_all.columns
has_volume = 'Volume' in df_all.columns

# ========== サイドバー：分析ツール ON/OFF ==========
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔧 分析ツール設定")

use_ma = st.sidebar.checkbox("📊 移動平均線 (MA)", value=True)
use_rsi = st.sidebar.checkbox("📉 RSI", value=False)
use_stoch = st.sidebar.checkbox("🔀 ストキャスティクス", value=False)
use_volume = st.sidebar.checkbox("📦 出来高フィルター", value=False) if has_volume else False

# ========== 移動平均パラメータ ==========
if use_ma:
    st.sidebar.markdown("### 📊 移動平均設定")
    short_ma = st.sidebar.number_input("短期MA日数", min_value=1, max_value=50, value=5)
    long_ma = st.sidebar.number_input("長期MA日数", min_value=5, max_value=200, value=25)
    ma_condition = st.sidebar.selectbox(
        "MA条件",
        ["短期MAが長期MAを上抜け（ゴールデンクロス）",
         "短期MAが長期MAより上",
         "終値が短期MAより上"]
    )

# ========== RSIパラメータ ==========
if use_rsi:
    st.sidebar.markdown("### 📉 RSI設定")
    rsi_period = st.sidebar.number_input("RSI期間", min_value=2, max_value=30, value=14)
    rsi_min = st.sidebar.number_input("RSI下限", min_value=0, max_value=100, value=30)
    rsi_max = st.sidebar.number_input("RSI上限", min_value=0, max_value=100, value=70)

# ========== ストキャスティクスパラメータ ==========
if use_stoch:
    st.sidebar.markdown("### 🔀 ストキャスティクス設定")
    stoch_k = st.sidebar.number_input("%K期間", min_value=1, max_value=30, value=14)
    stoch_d = st.sidebar.number_input("%D期間（SMA）", min_value=1, max_value=10, value=3)
    stoch_condition = st.sidebar.selectbox(
        "ストキャスティクス条件",
        ["%Kが%Dを上抜け（ゴールデンクロス）",
         "%Kが%Dより上",
         "%Kが20以下（売られすぎ）",
         "%Kが80以上（買われすぎ）"]
    )
    stoch_pos_min = st.sidebar.number_input("%K 最小値(%)", min_value=0, max_value=100, value=0)
    stoch_pos_max = st.sidebar.number_input("%K 最大値(%)", min_value=0, max_value=100, value=100)

# ========== 出来高パラメータ ==========
if use_volume and has_volume:
    st.sidebar.markdown("### 📦 出来高設定")
    vol_min = st.sidebar.number_input("最小出来高", min_value=0, value=100000, step=10000)

# ========== スクリーニング関数 ==========
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_stoch(df, k_period=14, d_period=3):
    low_min = df['Low'].rolling(k_period).min()
    high_max = df['High'].rolling(k_period).max()
    k = 100 * (df['Close'] - low_min) / (high_max - low_min)
    d = k.rolling(d_period).mean()
    return k, d

def screen_stock(df_stock):
    df_stock = df_stock.sort_values('Date').copy()
    results = []

    if use_ma:
        df_stock[f'MA{short_ma}'] = df_stock['Close'].rolling(short_ma).mean()
        df_stock[f'MA{long_ma}'] = df_stock['Close'].rolling(long_ma).mean()

        if df_stock[f'MA{short_ma}'].isna().all() or df_stock[f'MA{long_ma}'].isna().all():
            return False, df_stock
        df_stock = df_stock.dropna(subset=[f'MA{short_ma}', f'MA{long_ma}'])
        if len(df_stock) < 2:
            return False, df_stock

        last = df_stock.iloc[-1]
        prev = df_stock.iloc[-2]

        if ma_condition == "短期MAが長期MAを上抜け（ゴールデンクロス）":
            ok = (prev[f'MA{short_ma}'] <= prev[f'MA{long_ma}']) and (last[f'MA{short_ma}'] > last[f'MA{long_ma}'])
        elif ma_condition == "短期MAが長期MAより上":
            ok = last[f'MA{short_ma}'] > last[f'MA{long_ma}']
        else:
            ok = last['Close'] > last[f'MA{short_ma}']
        results.append(ok)

    if use_rsi:
        df_stock['RSI'] = calc_rsi(df_stock['Close'], rsi_period)
        df_stock = df_stock.dropna(subset=['RSI'])
        if len(df_stock) == 0:
            return False, df_stock
        last_rsi = df_stock['RSI'].iloc[-1]
        results.append(rsi_min <= last_rsi <= rsi_max)

    if use_stoch:
        df_stock['%K'], df_stock['%D'] = calc_stoch(df_stock, stoch_k, stoch_d)
        df_stock = df_stock.dropna(subset=['%K', '%D'])
        if len(df_stock) < 2:
            return False, df_stock

        last = df_stock.iloc[-1]
        prev = df_stock.iloc[-2]
        k_val = last['%K']
        d_val = last['%D']

        # %K範囲フィルター
        if not (stoch_pos_min <= k_val <= stoch_pos_max):
            return False, df_stock

        if stoch_condition == "%Kが%Dを上抜け（ゴールデンクロス）":
            ok = (prev['%K'] <= prev['%D']) and (last['%K'] > last['%D'])
        elif stoch_condition == "%Kが%Dより上":
            ok = k_val > d_val
        elif stoch_condition == "%Kが20以下（売られすぎ）":
            ok = k_val <= 20
        else:
            ok = k_val >= 80
        results.append(ok)

    if use_volume and has_volume:
        last_vol = df_stock['Volume'].iloc[-1]
        results.append(last_vol >= vol_min)

    if not results:
        return False, df_stock

    return all(results), df_stock

# ========== スクリーニング実行 ==========
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    run_all = st.button("🚀 全銘柄スクリーニング実行")
with col2:
    run_sample = st.button("🔬 サンプル100銘柄でテスト")
with col3:
    st.write("")

if run_all or run_sample:
    codes = df_all['Code'].unique()
    if run_sample:
        codes = codes[:100]

    matched = []
    progress = st.progress(0)
    status_text = st.empty()

    for i, code in enumerate(codes):
        df_stock = df_all[df_all['Code'] == code].copy()
        hit, df_result = screen_stock(df_stock)
        if hit:
            last_row = df_result.iloc[-1]
            row_data = {
                '証券コード': code,
                '最終日付': last_row['Date'].strftime('%Y-%m-%d'),
                '終値': last_row['Close'],
            }
            if has_name:
                row_data['銘柄名'] = df_stock['Name'].iloc[-1]
            if use_ma:
                row_data[f'MA{short_ma}'] = round(last_row.get(f'MA{short_ma}', np.nan), 2)
                row_data[f'MA{long_ma}'] = round(last_row.get(f'MA{long_ma}', np.nan), 2)
            if use_rsi:
                row_data['RSI'] = round(last_row.get('RSI', np.nan), 2)
            if use_stoch:
                row_data['%K'] = round(last_row.get('%K', np.nan), 2)
                row_data['%D'] = round(last_row.get('%D', np.nan), 2)
            matched.append(row_data)

        if i % 50 == 0:
            progress.progress(int((i + 1) / len(codes) * 100))
            status_text.text(f"処理中... {i+1}/{len(codes)} 銘柄")

    progress.progress(100)
    status_text.text(f"✅ 完了！ {len(matched)} 銘柄がヒットしました")

    # ========== 結果表示 ==========
    if matched:
        df_result = pd.DataFrame(matched)

        # 列の並び替え（銘柄名があれば前に）
        cols = ['証券コード']
        if has_name:
            cols.append('銘柄名')
        cols += [c for c in df_result.columns if c not in cols]
        df_result = df_result[cols]

        st.success(f"🎯 {len(df_result)} 銘柄がスクリーニング条件に一致しました")
        st.dataframe(df_result, use_container_width=True)

        # ダウンロード
        csv_out = df_result.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 結果をCSVでダウンロード",
            data=csv_out,
            file_name="screening_result.csv",
            mime="text/csv"
        )

        # ========== チャート表示 ==========
        st.markdown("---")
        st.subheader("📊 個別チャート表示")
        code_list = df_result['証券コード'].tolist()
        selected_code = st.selectbox("銘柄を選択", code_list)

        df_chart = df_all[df_all['Code'] == selected_code].sort_values('Date').copy()

        fig, axes = plt.subplots(
            2 if (use_rsi or use_stoch) else 1,
            1,
            figsize=(14, 8 if (use_rsi or use_stoch) else 5),
            sharex=True
        )
        if not isinstance(axes, np.ndarray):
            axes = [axes]

        ax1 = axes[0]
        ax1.plot(df_chart['Date'], df_chart['Close'], label='終値', color='black', linewidth=1.2)

        if use_ma:
            ma_s = df_chart['Close'].rolling(short_ma).mean()
            ma_l = df_chart['Close'].rolling(long_ma).mean()
            ax1.plot(df_chart['Date'], ma_s, label=f'MA{short_ma}', color='blue', linewidth=1)
            ax1.plot(df_chart['Date'], ma_l, label=f'MA{long_ma}', color='red', linewidth=1)

        ax1.set_title(f"証券コード: {selected_code}", fontsize=14)
        ax1.set_ylabel("株価 (円)")
        ax1.legend(loc='upper left')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.grid(True, alpha=0.3)

        if len(axes) > 1:
            ax2 = axes[1]
            if use_rsi:
                rsi_vals = calc_rsi(df_chart['Close'], rsi_period)
                ax2.plot(df_chart['Date'], rsi_vals, label='RSI', color='purple')
                ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
                ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
                ax2.set_ylabel("RSI")
                ax2.legend(loc='upper left')
            elif use_stoch:
                k_vals, d_vals = calc_stoch(df_chart, stoch_k, stoch_d)
                ax2.plot(df_chart['Date'], k_vals, label='%K', color='blue')
                ax2.plot(df_chart['Date'], d_vals, label='%D', color='red')
                ax2.axhline(80, color='red', linestyle='--', alpha=0.5)
                ax2.axhline(20, color='green', linestyle='--', alpha=0.5)
                ax2.set_ylabel("ストキャスティクス")
                ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    else:
        st.warning("⚠️ 条件に一致する銘柄が見つかりませんでした")
        st.info("💡 条件を緩めてみてください（例：ゴールデンクロス→MAより上、期間を短縮）")