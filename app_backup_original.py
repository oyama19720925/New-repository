import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ========== 繝壹・繧ｸ險ｭ螳・==========
st.set_page_config(page_title="譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ", layout="wide")
st.title("嶋 譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ繧ｷ繧ｹ繝・Β")

# ========== CSV繝輔ぃ繧､繝ｫ讀懷・ ==========
csv_files = glob.glob("*.csv")
if not csv_files:
    st.error("笶・CSV繝輔ぃ繧､繝ｫ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縲Ｔtock_system繝輔か繝ｫ繝縺ｫCSV繧堤ｽｮ縺・※縺上□縺輔＞縲・)
    st.stop()

selected_csv = st.sidebar.selectbox("唐 CSV繝輔ぃ繧､繝ｫ繧帝∈謚・, csv_files)

# ========== 繝・・繧ｿ隱ｭ縺ｿ霎ｼ縺ｿ ==========
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype={'Code': str})
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 笘・CoName 縺後↑縺代ｌ縺ｰ stock_master.csv 縺九ｉ繝槭・繧ｸ
    if 'CoName' not in df.columns:
        master_path = os.path.join(os.path.dirname(os.path.abspath(path)), 'stock_master.csv')
        if os.path.exists(master_path):
            master = pd.read_csv(master_path, dtype={'Code': str})
            cols = ['Code']
            for c in ['CoName', 'S33Nm', 'MktNm']:
                if c in master.columns:
                    cols.append(c)
            df = df.merge(master[cols], on='Code', how='left')
    
    # 笘・Vo 縺後↑縺代ｌ縺ｰ 0 縺ｧ蝓九ａ繧・
    if 'Vo' not in df.columns:
        df['Vo'] = 0
    
    return df

df_all = load_data(selected_csv)

# ========== 蛻怜錐螳夂ｾｩ ==========
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

# ========== 蛻怜錐繝√ぉ繝・け ==========
required_cols = [COL_DATE, COL_CODE, COL_NAME, COL_OPEN, COL_HIGH, COL_LOW, COL_CLOSE, COL_VOLUME]
missing_cols = [c for c in required_cols if c not in df_all.columns]
if missing_cols:
    st.error(f"笶・蠢・ｦ√↑蛻励′隕九▽縺九ｊ縺ｾ縺帙ｓ: {missing_cols}")
    st.write("搭 螳滄圀縺ｮ蛻怜錐:", df_all.columns.tolist())
    st.stop()

# ========== 繧ｵ繧､繝峨ヰ繝ｼ・壹ヵ繧｣繝ｫ繧ｿ ==========
st.sidebar.header("肌 繝輔ぅ繝ｫ繧ｿ險ｭ螳・)

# --- 譛滄俣 ---
st.sidebar.subheader("套 譛滄俣")
date_min = df_all[COL_DATE].min().date()
date_max = df_all[COL_DATE].max().date()
start_date = st.sidebar.date_input("髢句ｧ区律", value=date_min, min_value=date_min, max_value=date_max)
end_date   = st.sidebar.date_input("邨ゆｺ・律", value=date_max, min_value=date_min, max_value=date_max)

# --- 蟶ょｴ ---
st.sidebar.subheader("召 蟶ょｴ")
if COL_MARKET in df_all.columns:
    markets = sorted(df_all[COL_MARKET].dropna().unique().tolist())
    selected_markets = st.sidebar.multiselect("蟶ょｴ繧帝∈謚橸ｼ域悴驕ｸ謚・蜈ｨ縺ｦ・・, markets)
else:
    selected_markets = []

# --- 讌ｭ遞ｮ ---
st.sidebar.subheader("少 讌ｭ遞ｮ")
if COL_SECTOR in df_all.columns:
    sectors = sorted(df_all[COL_SECTOR].dropna().unique().tolist())
    selected_sectors = st.sidebar.multiselect("讌ｭ遞ｮ繧帝∈謚橸ｼ域悴驕ｸ謚・蜈ｨ縺ｦ・・, sectors)
else:
    selected_sectors = []

# ========== 繧ｵ繧､繝峨ヰ繝ｼ・壼・譫舌ヤ繝ｼ繝ｫ ==========
st.sidebar.header("投 蛻・梵繝・・繝ｫ")

# --- 遘ｻ蜍募ｹｳ蝮・---
st.sidebar.subheader("悼 遘ｻ蜍募ｹｳ蝮・)
use_ma = st.sidebar.checkbox("遘ｻ蜍募ｹｳ蝮・ｒ菴ｿ逕ｨ", value=True)
if use_ma:
    ma_short = st.sidebar.number_input("遏ｭ譛櫪A・域律・・, min_value=1, max_value=200, value=5)
    ma_long  = st.sidebar.number_input("髟ｷ譛櫪A・域律・・, min_value=1, max_value=200, value=25)
    ma_cond  = st.sidebar.selectbox("譚｡莉ｶ", ['繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ', '遏ｭ譛・> 髟ｷ譛・, '遏ｭ譛・< 髟ｷ譛・])
else:
    ma_short = 5
    ma_long  = 25
    ma_cond  = '繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ'

# --- RSI ---
st.sidebar.subheader("投 RSI")
use_rsi = st.sidebar.checkbox("RSI繧剃ｽｿ逕ｨ", value=False)
if use_rsi:
    rsi_period = st.sidebar.number_input("RSI譛滄俣・域律・・, min_value=2, max_value=100, value=14)
    rsi_min    = st.sidebar.slider("RSI 譛蟆丞､", 0, 100, 30)
    rsi_max    = st.sidebar.slider("RSI 譛螟ｧ蛟､", 0, 100, 70)
else:
    rsi_period = 14
    rsi_min    = 30
    rsi_max    = 70

# --- 繧ｹ繝医く繝｣繧ｹ繝・ぅ繧ｯ繧ｹ ---
st.sidebar.subheader("嶋 繧ｹ繝医く繝｣繧ｹ繝・ぅ繧ｯ繧ｹ")
use_stoch = st.sidebar.checkbox("繧ｹ繝医く繝｣繧ｹ繝・ぅ繧ｯ繧ｹ繧剃ｽｿ逕ｨ", value=False)
if use_stoch:
    stoch_k   = st.sidebar.number_input("%K譛滄俣・域律・・, min_value=1, max_value=100, value=14)
    stoch_d   = st.sidebar.number_input("%D譛滄俣・域律・・, min_value=1, max_value=100, value=3)
    stoch_cond = st.sidebar.selectbox("譚｡莉ｶ", ['繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ', '%K > %D', '%K < %D'])
    stoch_pos_filter = st.sidebar.checkbox("%K 縺ｮ遽・峇縺ｧ繝輔ぅ繝ｫ繧ｿ", value=False)
    if stoch_pos_filter:
        stoch_pos_min = st.sidebar.slider("%K 譛蟆丞､・・・・, 0, 100, 20)
        stoch_pos_max = st.sidebar.slider("%K 譛螟ｧ蛟､・・・・, 0, 100, 80)
    else:
        stoch_pos_min = 0
        stoch_pos_max = 100
else:
    stoch_k   = 14
    stoch_d   = 3
    stoch_cond = '繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ'
    stoch_pos_filter = False
    stoch_pos_min = 0
    stoch_pos_max = 100

# --- 蜃ｺ譚･鬮・---
st.sidebar.subheader("逃 蜃ｺ譚･鬮・)
use_volume = st.sidebar.checkbox("蜃ｺ譚･鬮倥ｒ菴ｿ逕ｨ", value=False)
if use_volume:
    vol_days = st.sidebar.number_input("蟷ｳ蝮・律謨ｰ", min_value=1, max_value=60, value=5)
    vol_min  = st.sidebar.number_input("譛蟆丞・譚･鬮假ｼ亥ｹｳ蝮・ｼ・, min_value=0, value=100000, step=10000)
else:
    vol_days = 5
    vol_min  = 100000

# ========== 繝・・繧ｿ邨槭ｊ霎ｼ縺ｿ ==========
target_df = df_all[
    (df_all[COL_DATE] >= pd.Timestamp(start_date)) &
    (df_all[COL_DATE] <= pd.Timestamp(end_date))
].copy()

if selected_markets:
    target_df = target_df[target_df[COL_MARKET].isin(selected_markets)]

if selected_sectors:
    target_df = target_df[target_df[COL_SECTOR].isin(selected_sectors)]

st.write(f"搭 蟇ｾ雎｡繝・・繧ｿ: {len(target_df):,} 陦・/ {target_df[COL_CODE].nunique():,} 驫俶氛")

# ========== 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ髢｢謨ｰ ==========
def do_screening(df):
    results = []

    for code, group in df.groupby(COL_CODE):
        group = group.sort_values(COL_DATE).reset_index(drop=True)

        if len(group) < 2:
            continue

        last = group.iloc[-1]

        # 驫俶氛蜷阪ｒ螳牙・縺ｫ蜿門ｾ・
        name = last[COL_NAME] if COL_NAME in group.columns else ''

        close  = group[COL_CLOSE].values.astype(float)
        high   = group[COL_HIGH].values.astype(float)
        low    = group[COL_LOW].values.astype(float)
        volume = group[COL_VOLUME].values.astype(float)

        passed = True

        # ========== 遘ｻ蜍募ｹｳ蝮・==========
        if use_ma:
            if len(close) < ma_long:
                continue
            ma_s = pd.Series(close).rolling(ma_short).mean()
            ma_l = pd.Series(close).rolling(ma_long).mean()
            if pd.isna(ma_s.iloc[-1]) or pd.isna(ma_l.iloc[-1]):
                continue
            if len(ma_s) < 2 or len(ma_l) < 2:
                continue
            if ma_cond == '繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ':
                if not (ma_s.iloc[-2] < ma_l.iloc[-2] and ma_s.iloc[-1] > ma_l.iloc[-1]):
                    passed = False
            elif ma_cond == '遏ｭ譛・> 髟ｷ譛・:
                if not (ma_s.iloc[-1] > ma_l.iloc[-1]):
                    passed = False
            elif ma_cond == '遏ｭ譛・< 髟ｷ譛・:
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

        # ========== 繧ｹ繝医く繝｣繧ｹ繝・ぅ繧ｯ繧ｹ ==========
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

            if stoch_cond == '繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ':
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

        # ========== 蜃ｺ譚･鬮・==========
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
                '驫俶氛繧ｳ繝ｼ繝・: code,
                '驫俶氛蜷・:     name,
                '邨ょ､':       last[COL_CLOSE],
                '譌･莉・:       last[COL_DATE],
            })

    return pd.DataFrame(results)

# ========== 螳溯｡後・繧ｿ繝ｳ ==========
col1, col2 = st.columns(2)

with col1:
    run_btn = st.button("剥 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ螳溯｡・, type="primary", use_container_width=True)

with col2:
    run_all_btn = st.button("搭 蜈ｨ驫俶氛陦ｨ遉ｺ・域擅莉ｶ縺ｪ縺暦ｼ・, use_container_width=True)

# ========== 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ螳溯｡・==========
if run_btn:
    if not use_ma and not use_rsi and not use_stoch and not use_volume:
        st.warning("笞・・蛻・梵繝・・繝ｫ縺悟・縺ｦOFF縺ｧ縺吶ょｰ代↑縺上→繧・縺､繧丹N縺ｫ縺励※縺上□縺輔＞縲・)
    else:
        with st.spinner("竢ｳ 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ荳ｭ..."):
            result_df = do_screening(target_df)

        if result_df.empty:
            st.warning("笞・・譚｡莉ｶ縺ｫ蜷医≧驫俶氛縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縺ｧ縺励◆縲よ擅莉ｶ繧堤ｷｩ繧√※縺ｿ縺ｦ縺上□縺輔＞縲・)
        else:
            st.success(f"笨・{len(result_df)} 驫俶氛縺梧擅莉ｶ縺ｫ荳閾ｴ縺励∪縺励◆・・)
            st.dataframe(result_df, use_container_width=True)

            # 繝繧ｦ繝ｳ繝ｭ繝ｼ繝・
            csv_out = result_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="沈 邨先棡繧辰SV繝繧ｦ繝ｳ繝ｭ繝ｼ繝・,
                data=csv_out,
                file_name="screening_result.csv",
                mime="text/csv"
            )

# ========== 蜈ｨ驫俶氛陦ｨ遉ｺ ==========
if run_all_btn:
    with st.spinner("竢ｳ 髮・ｨ井ｸｭ..."):
        summary_list = []
        for code, group in target_df.groupby(COL_CODE):
            group = group.sort_values(COL_DATE).reset_index(drop=True)
            last = group.iloc[-1]
            name = last[COL_NAME] if COL_NAME in group.columns else ''
            summary_list.append({
                '驫俶氛繧ｳ繝ｼ繝・: code,
                '驫俶氛蜷・:     name,
                '邨ょ､':       last[COL_CLOSE],
                '譌･莉・:       last[COL_DATE],
            })
        summary_df = pd.DataFrame(summary_list)

    st.success(f"搭 蜈ｨ {len(summary_df)} 驫俶氛")
    st.dataframe(summary_df, use_container_width=True)

    csv_out = summary_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="沈 蜈ｨ驫俶氛CSV繝繧ｦ繝ｳ繝ｭ繝ｼ繝・,
        data=csv_out,
        file_name="all_stocks.csv",
        mime="text/csv"
    )

# ========== 繝√Ε繝ｼ繝郁｡ｨ遉ｺ ==========
st.header("投 蛟句挨繝√Ε繝ｼ繝・)
chart_code = st.text_input("驫俶氛繧ｳ繝ｼ繝峨ｒ蜈･蜉幢ｼ井ｾ・ 7203・・, value="")

if chart_code:
    chart_df = df_all[df_all[COL_CODE] == chart_code].sort_values(COL_DATE).reset_index(drop=True)

    if chart_df.empty:
        st.warning(f"笞・・驫俶氛繧ｳ繝ｼ繝・{chart_code} 縺ｮ繝・・繧ｿ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縲・)
    else:
        name_val = chart_df.iloc[-1][COL_NAME] if COL_NAME in chart_df.columns else ''
        st.subheader(f"{chart_code}  {name_val}")

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.6, 0.2, 0.2],
            vertical_spacing=0.05,
            subplot_titles=("繝ｭ繝ｼ繧ｽ繧ｯ雜ｳ + MA", "蜃ｺ譚･鬮・, "RSI / 繧ｹ繝医く繝｣繧ｹ繝・ぅ繧ｯ繧ｹ")
        )

        # 繝ｭ繝ｼ繧ｽ繧ｯ雜ｳ
        fig.add_trace(go.Candlestick(
            x=chart_df[COL_DATE],
            open=chart_df[COL_OPEN],
            high=chart_df[COL_HIGH],
            low=chart_df[COL_LOW],
            close=chart_df[COL_CLOSE],
            name="繝ｭ繝ｼ繧ｽ繧ｯ雜ｳ"
        ), row=1, col=1)

        # 遘ｻ蜍募ｹｳ蝮・ｷ・
        for period, color in [(5, 'blue'), (25, 'orange'), (75, 'green')]:
            ma = chart_df[COL_CLOSE].rolling(period).mean()
            fig.add_trace(go.Scatter(
                x=chart_df[COL_DATE], y=ma,
                name=f"MA{period}", line=dict(color=color, width=1)
            ), row=1, col=1)

        # 蜃ｺ譚･鬮・
        fig.add_trace(go.Bar(
            x=chart_df[COL_DATE],
            y=chart_df[COL_VOLUME],
            name="蜃ｺ譚･鬮・,
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

        # 繧ｹ繝医く繝｣繧ｹ繝・ぅ繧ｯ繧ｹ
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
