import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob

# =============================================
# ページ設定
# =============================================
st.set_page_config(
    page_title="バックテスト比較ダッシュボード",
    layout="wide"
)

st.title("📊 バックテスト比較ダッシュボード")
st.markdown("---")

# =============================================
# データ読み込み
# =============================================
@st.cache_data
def load_data():
    files = glob.glob("*.csv")
    csv_files = [f for f in files if "stocks_OHLC" in f or "stock" in f.lower()]

    if not csv_files:
        return pd.DataFrame()

    path = sorted(csv_files)[-1]
    df = None
    for enc in ['utf-8', 'utf-8-sig', 'cp932', 'shift-jis']:
        try:
            df = pd.read_csv(path, parse_dates=['Date'], encoding=enc)
            break
        except:
            continue

    if df is None:
        return pd.DataFrame()

    col = df.columns.tolist()
    rename_map = {}
    if 'MktNm'  in col: rename_map['MktNm']  = 'Market'
    if 'CoName' in col: rename_map['CoName'] = 'Name'
    if 'S33Nm'  in col: rename_map['S33Nm']  = 'Sector'
    if 'O'      in col: rename_map['O']       = 'Open'
    if 'H'      in col: rename_map['H']       = 'High'
    if 'L'      in col: rename_map['L']       = 'Low'
    if 'C'      in col: rename_map['C']       = 'Close'
    if 'Vo'     in col: rename_map['Vo']      = 'Volume'
    df.rename(columns=rename_map, inplace=True)
    df['Code'] = df['Code'].astype(str)
    return df

# =============================================
# テクニカル指標計算
# =============================================
def calc_indicators(df, params):
    d = df.copy().sort_values('Date').reset_index(drop=True)

    s, l = params['ma_short'], params['ma_long']
    d['MA_s'] = d['Close'].rolling(s).mean()
    d['MA_l'] = d['Close'].rolling(l).mean()

    rsi_p = params['rsi_period']
    delta = d['Close'].diff()
    gain  = delta.clip(lower=0).rolling(rsi_p).mean()
    loss  = (-delta.clip(upper=0)).rolling(rsi_p).mean()
    rs    = gain / loss.replace(0, np.nan)
    d['RSI'] = 100 - 100 / (1 + rs)

    k_p, d_p = params['stoch_k'], params['stoch_d']
    lo  = d['Low'].rolling(k_p).min()
    hi  = d['High'].rolling(k_p).max()
    d['%K'] = (d['Close'] - lo) / (hi - lo + 1e-9) * 100
    d['%D'] = d['%K'].rolling(d_p).mean()

    d['EMA12']       = d['Close'].ewm(span=12).mean()
    d['EMA26']       = d['Close'].ewm(span=26).mean()
    d['MACD']        = d['EMA12'] - d['EMA26']
    d['Signal_MACD'] = d['MACD'].ewm(span=9).mean()

    bb_p = params['bb_period']
    d['BB_mid'] = d['Close'].rolling(bb_p).mean()
    d['BB_std'] = d['Close'].rolling(bb_p).std()
    d['BB_up']  = d['BB_mid'] + 2 * d['BB_std']
    d['BB_lo']  = d['BB_mid'] - 2 * d['BB_std']
    d['BB_%B']  = (d['Close'] - d['BB_lo']) / \
                  (d['BB_up'] - d['BB_lo'] + 1e-9) * 100

    d['Vol_MA'] = d['Volume'].rolling(20).mean()
    return d

# =============================================
# スクリーニング判定
# =============================================
def screen_stock(d, params, flags):
    if len(d) < 5:
        return False, {}

    last = d.iloc[-1]
    prev = d.iloc[-2]
    info = {}
    passed = True

    if flags.get('use_ma', False):
        gc    = (prev['MA_s'] <= prev['MA_l']) and (last['MA_s'] > last['MA_l'])
        ma_ok = gc if params['ma_cond'] == 'ゴールデンクロス' else \
                (last['MA_s'] > last['MA_l'])
        info['MA'] = '✅' if ma_ok else '❌'
        if not ma_ok:
            passed = False

    if flags.get('use_rsi', False):
        rsi_val = last['RSI']
        rsi_ok  = params['rsi_lo'] <= rsi_val <= params['rsi_hi']
        info['RSI'] = f"{'✅' if rsi_ok else '❌'} {rsi_val:.1f}"
        if not rsi_ok:
            passed = False

    if flags.get('use_stoch', False):
        k_val = last['%K']
        d_val = last['%D']
        pk    = prev['%K']
        pd_   = prev['%D']
        cond  = params['stoch_cond']
        if cond == '%Kが%Dを上抜け（GC）':
            stoch_ok = (pk <= pd_) and (k_val > d_val)
        elif cond == '%K < 20（売られすぎ）':
            stoch_ok = k_val < 20
        elif cond == '%K > 80（買われすぎ）':
            stoch_ok = k_val > 80
        else:
            stoch_ok = params['stoch_lo'] <= k_val <= params['stoch_hi']
        info['Stoch'] = f"{'✅' if stoch_ok else '❌'} K:{k_val:.1f} D:{d_val:.1f}"
        if not stoch_ok:
            passed = False

    if flags.get('use_macd', False):
        macd_gc = (prev['MACD'] <= prev['Signal_MACD']) and \
                  (last['MACD'] > last['Signal_MACD'])
        info['MACD'] = '✅ GC' if macd_gc else '❌'
        if not macd_gc:
            passed = False

    if flags.get('use_bb', False):
        bb_ok = last['BB_%B'] <= params['bb_threshold']
        info['BB'] = f"{'✅' if bb_ok else '❌'} %B:{last['BB_%B']:.1f}"
        if not bb_ok:
            passed = False

    if flags.get('use_vol', False):
        vol_ok = last['Volume'] >= last['Vol_MA'] * params['vol_ratio']
        info['Vol'] = '✅' if vol_ok else '❌'
        if not vol_ok:
            passed = False

    info['Close']  = last['Close']
    info['Change'] = (last['Close'] - prev['Close']) / prev['Close'] * 100 \
                     if prev['Close'] != 0 else 0
    return passed, info

# =============================================
# バックテスト
# =============================================
def run_backtest(df_stock, params, flags, initial_capital=1_000_000):
    df = df_stock.copy().sort_values('Date').reset_index(drop=True)

    s, l = params['ma_short'], params['ma_long']
    df['MA_s'] = df['Close'].rolling(s).mean()
    df['MA_l'] = df['Close'].rolling(l).mean()

    rsi_p = params['rsi_period']
    delta = df['Close'].diff()
    gain  = delta.clip(lower=0).rolling(rsi_p).mean()
    loss  = (-delta.clip(upper=0)).rolling(rsi_p).mean()
    rs    = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - 100 / (1 + rs)

    k_p, d_p = params['stoch_k'], params['stoch_d']
    lo  = df['Low'].rolling(k_p).min()
    hi  = df['High'].rolling(k_p).max()
    df['%K'] = (df['Close'] - lo) / (hi - lo + 1e-9) * 100
    df['%D'] = df['%K'].rolling(d_p).mean()

    df['EMA12']       = df['Close'].ewm(span=12).mean()
    df['EMA26']       = df['Close'].ewm(span=26).mean()
    df['MACD']        = df['EMA12'] - df['EMA26']
    df['Signal_MACD'] = df['MACD'].ewm(span=9).mean()

    bb_p = params['bb_period']
    df['BB_mid'] = df['Close'].rolling(bb_p).mean()
    df['BB_std'] = df['Close'].rolling(bb_p).std()
    df['BB_up']  = df['BB_mid'] + 2 * df['BB_std']
    df['BB_lo']  = df['BB_mid'] - 2 * df['BB_std']
    df['BB_%B']  = (df['Close'] - df['BB_lo']) / \
                   (df['BB_up'] - df['BB_lo'] + 1e-9) * 100

    if 'Volume' in df.columns and df['Volume'].sum() > 0:
        df['Vol_MA'] = df['Volume'].rolling(20).mean()
    else:
        df['Vol_MA'] = 1
        df['Volume'] = 1

    def is_buy_signal(i):
        if i < 1:
            return False
        row  = df.loc[i]
        prev = df.loc[i - 1]
        conditions = []

        if flags.get('use_ma', False):
            if params['ma_cond'] == 'ゴールデンクロス':
                conditions.append(
                    (prev['MA_s'] <= prev['MA_l']) and (row['MA_s'] > row['MA_l']))
            else:
                conditions.append(row['MA_s'] > row['MA_l'])

        if flags.get('use_rsi', False):
            conditions.append(params['rsi_lo'] <= row['RSI'] <= params['rsi_hi'])

        if flags.get('use_stoch', False):
            k_val = row['%K']
            d_val = row['%D']
            pk    = prev['%K']
            pd_   = prev['%D']
            cond  = params['stoch_cond']
            if cond == '%Kが%Dを上抜け（GC）':
                conditions.append((pk <= pd_) and (k_val > d_val))
            elif cond == '%K < 20（売られすぎ）':
                conditions.append(k_val < 20)
            elif cond == '%K > 80（買われすぎ）':
                conditions.append(k_val > 80)
            else:
                conditions.append(params['stoch_lo'] <= k_val <= params['stoch_hi'])

        if flags.get('use_macd', False):
            conditions.append(
                (prev['MACD'] <= prev['Signal_MACD']) and
                (row['MACD']  >  row['Signal_MACD']))

        if flags.get('use_bb', False):
            conditions.append(row['BB_%B'] <= params['bb_threshold'])

        if flags.get('use_vol', False):
            conditions.append(row['Volume'] >= row['Vol_MA'] * params['vol_ratio'])

        if len(conditions) == 0:
            return False
        return all(conditions)

    def is_sell_signal(i):
        if i < 1:
            return False
        row  = df.loc[i]
        prev = df.loc[i - 1]
        sell_conditions = []

        if flags.get('use_ma', False):
            if params['ma_cond'] == 'ゴールデンクロス':
                sell_conditions.append(
                    (prev['MA_s'] >= prev['MA_l']) and (row['MA_s'] < row['MA_l']))
            else:
                sell_conditions.append(row['MA_s'] < row['MA_l'])

        if flags.get('use_rsi', False):
            sell_conditions.append(
                not (params['rsi_lo'] <= row['RSI'] <= params['rsi_hi']))

        if flags.get('use_stoch', False):
            k_val = row['%K']
            d_val = row['%D']
            pk    = prev['%K']
            pd_   = prev['%D']
            cond  = params['stoch_cond']
            if cond == '%Kが%Dを上抜け（GC）':
                sell_conditions.append((pk >= pd_) and (k_val < d_val))
            elif cond == '%K < 20（売られすぎ）':
                sell_conditions.append(k_val >= 20)
            elif cond == '%K > 80（買われすぎ）':
                sell_conditions.append(k_val <= 80)
            else:
                sell_conditions.append(
                    not (params['stoch_lo'] <= k_val <= params['stoch_hi']))

        if flags.get('use_macd', False):
            sell_conditions.append(
                (prev['MACD'] >= prev['Signal_MACD']) and
                (row['MACD']  <  row['Signal_MACD']))

        if flags.get('use_bb', False):
            sell_conditions.append(row['BB_%B'] >= 80)

        if len(sell_conditions) == 0:
            return False
        return any(sell_conditions)

    # ── バックテスト本体 ──
    trades       = []
    position     = 0
    buy_price    = 0
    buy_date     = None
    shares       = 0
    capital      = initial_capital
    equity       = [initial_capital]
    equity_dates = [df.loc[0, 'Date']]
    min_data     = max(l, rsi_p, k_p, bb_p, 26) + 10

    for i in range(1, len(df)):
        if i < min_data:
            equity.append(capital + position * shares * df.loc[i, 'Close'])
            equity_dates.append(df.loc[i, 'Date'])
            continue

        price = df.loc[i, 'Close']

        if position == 0 and is_buy_signal(i - 1):
            buy_price = price
            buy_date  = df.loc[i, 'Date']
            shares    = max(100, int(capital // price // 100) * 100)
            capital  -= shares * buy_price
            position  = 1

        elif position == 1 and is_sell_signal(i - 1):
            sell_price = price
            pnl        = (sell_price - buy_price) * shares
            capital   += shares * sell_price
            hold_days  = (df.loc[i, 'Date'] - buy_date).days
            trades.append({
                '買日':      buy_date,
                '売日':      df.loc[i, 'Date'],
                '買値':      buy_price,
                '売値':      sell_price,
                '株数':      shares,
                '損益(円)':  round(pnl),
                '損益率(%)': round((sell_price - buy_price) / buy_price * 100, 2),
                '保有日数':  hold_days
            })
            position = 0

        equity.append(capital + position * shares * df.loc[i, 'Close'])
        equity_dates.append(df.loc[i, 'Date'])

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame({'Date': equity_dates, 'Equity': equity})
    return trades_df, equity_df

# =============================================
# チャート描画（ローソク足 + 指標）
# =============================================
def draw_chart(d, code, name, params, flags):
    rows   = 1
    row_h  = [4]
    specs  = [[ {"type": "candlestick"} ]]

    if flags.get('use_rsi', False)   or flags.get('use_stoch', False):
        rows += 1; row_h.append(2); specs.append([{"type":"scatter"}])
    if flags.get('use_macd', False):
        rows += 1; row_h.append(2); specs.append([{"type":"scatter"}])

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_h,
        vertical_spacing=0.03
    )

    # ローソク足
    fig.add_trace(go.Candlestick(
        x=d['Date'], open=d['Open'], high=d['High'],
        low=d['Low'], close=d['Close'],
        name='Price', increasing_line_color='red',
        decreasing_line_color='blue'
    ), row=1, col=1)

    # 移動平均
    if flags.get('use_ma', False):
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['MA_s'],
            name=f'MA{params["ma_short"]}',
            line=dict(color='orange', width=1)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['MA_l'],
            name=f'MA{params["ma_long"]}',
            line=dict(color='purple', width=1)
        ), row=1, col=1)

    # ボリンジャーバンド
    if flags.get('use_bb', False):
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['BB_up'],
            name='BB+2σ', line=dict(color='gray', dash='dot', width=1)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['BB_lo'],
            name='BB-2σ', line=dict(color='gray', dash='dot', width=1),
            fill='tonexty', fillcolor='rgba(128,128,128,0.1)'
        ), row=1, col=1)

    # RSI / Stoch
    r2 = 2
    if flags.get('use_rsi', False):
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['RSI'],
            name='RSI', line=dict(color='green', width=1)
        ), row=r2, col=1)
        fig.add_hline(y=70, line_dash='dot', line_color='red',   row=r2, col=1)
        fig.add_hline(y=30, line_dash='dot', line_color='blue',  row=r2, col=1)

    if flags.get('use_stoch', False):
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['%K'],
            name='%K', line=dict(color='blue', width=1)
        ), row=r2, col=1)
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['%D'],
            name='%D', line=dict(color='red', width=1)
        ), row=r2, col=1)

    if flags.get('use_rsi', False) or flags.get('use_stoch', False):
        r2 += 1

    # MACD
    if flags.get('use_macd', False):
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['MACD'],
            name='MACD', line=dict(color='blue', width=1)
        ), row=r2, col=1)
        fig.add_trace(go.Scatter(
            x=d['Date'], y=d['Signal_MACD'],
            name='Signal', line=dict(color='red', width=1)
        ), row=r2, col=1)
        hist_color = ['red' if v >= 0 else 'blue'
                      for v in (d['MACD'] - d['Signal_MACD'])]
        fig.add_trace(go.Bar(
            x=d['Date'], y=d['MACD'] - d['Signal_MACD'],
            name='Hist', marker_color=hist_color, opacity=0.5
        ), row=r2, col=1)

    fig.update_layout(
        title=f"{code} {name}",
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

# =============================================
# 損益曲線チャート
# =============================================
def draw_equity(equity_df, trades_df, code, name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_df['Date'], y=equity_df['Equity'],
        mode='lines', name='資産推移',
        line=dict(color='royalblue', width=2),
        fill='tozeroy', fillcolor='rgba(65,105,225,0.1)'
    ))

    if len(trades_df) > 0:
        wins  = trades_df[trades_df['損益(円)'] >= 0]
        loses = trades_df[trades_df['損益(円)'] <  0]
        # 売り日でマーク
        for _, row in wins.iterrows():
            eq_val = equity_df[equity_df['Date'] == row['売日']]['Equity']
            if len(eq_val) > 0:
                fig.add_trace(go.Scatter(
                    x=[row['売日']], y=[eq_val.values[0]],
                    mode='markers',
                    marker=dict(color='red', size=8, symbol='triangle-up'),
                    name='利確', showlegend=False
                ))
        for _, row in loses.iterrows():
            eq_val = equity_df[equity_df['Date'] == row['売日']]['Equity']
            if len(eq_val) > 0:
                fig.add_trace(go.Scatter(
                    x=[row['売日']], y=[eq_val.values[0]],
                    mode='markers',
                    marker=dict(color='blue', size=8, symbol='triangle-down'),
                    name='損切', showlegend=False
                ))

    fig.update_layout(
        title=f"📈 {code} {name} 損益曲線",
        height=300,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

# =============================================
# サマリー計算
# =============================================
def calc_summary(trades_df, equity_df, initial_capital):
    if len(trades_df) == 0:
        return {
            '総トレード数': 0, '勝率(%)': 0,
            '総損益(円)': 0, '最終資産(円)': initial_capital,
            'リターン(%)': 0, '最大DD(%)': 0,
            '平均保有日数': 0
        }

    wins      = trades_df[trades_df['損益(円)'] >= 0]
    total_pnl = trades_df['損益(円)'].sum()
    final_eq  = equity_df['Equity'].iloc[-1]

    # 最大ドローダウン
    eq        = equity_df['Equity']
    roll_max  = eq.cummax()
    dd        = (eq - roll_max) / roll_max * 100
    max_dd    = dd.min()

    return {
        '総トレード数':  len(trades_df),
        '勝率(%)':      round(len(wins) / len(trades_df) * 100, 1),
        '総損益(円)':   round(total_pnl),
        '最終資産(円)': round(final_eq),
        'リターン(%)':  round((final_eq - initial_capital) / initial_capital * 100, 2),
        '最大DD(%)':    round(max_dd, 2),
        '平均保有日数': round(trades_df['保有日数'].mean(), 1)
    }

# =============================================
# サイドバー：パラメータ設定
# =============================================
st.sidebar.title("⚙️ パラメータ設定")

# ── インジケーター ON/OFF ──
st.sidebar.markdown("### 🔘 インジケーター選択")
use_ma    = st.sidebar.checkbox("移動平均",          value=True,  key='ma')
use_rsi   = st.sidebar.checkbox("RSI",               value=False, key='rsi')
use_stoch = st.sidebar.checkbox("ストキャスティクス", value=False, key='stoch')
use_macd  = st.sidebar.checkbox("MACD",              value=False, key='macd')
use_bb    = st.sidebar.checkbox("ボリンジャーバンド", value=False, key='bb')
use_vol   = st.sidebar.checkbox("出来高",             value=False, key='vol')

flags = {
    'use_ma':    use_ma,
    'use_rsi':   use_rsi,
    'use_stoch': use_stoch,
    'use_macd':  use_macd,
    'use_bb':    use_bb,
    'use_vol':   use_vol
}

# ── 移動平均 ──
if use_ma:
    st.sidebar.markdown("#### 📉 移動平均")
    ma_short = st.sidebar.slider("短期MA", 3, 30, 5)
    ma_long  = st.sidebar.slider("長期MA", 10, 100, 25)
    ma_cond  = st.sidebar.selectbox(
        "条件", ['ゴールデンクロス', '短期>長期'])
else:
    ma_short, ma_long, ma_cond = 5, 25, 'ゴールデンクロス'

# ── RSI ──
if use_rsi:
    st.sidebar.markdown("#### 📊 RSI")
    rsi_period = st.sidebar.slider("RSI期間", 5, 30, 14)
    rsi_lo     = st.sidebar.slider("RSI 下限", 0, 50, 30)
    rsi_hi     = st.sidebar.slider("RSI 上限", 50, 100, 70)
else:
    rsi_period, rsi_lo, rsi_hi = 14, 30, 70

# ── ストキャスティクス ──
if use_stoch:
    st.sidebar.markdown("#### 🎯 ストキャスティクス")
    stoch_k   = st.sidebar.slider("%K期間", 3, 30, 14)
    stoch_d   = st.sidebar.slider("%D期間", 2, 10, 3)
    stoch_cond = st.sidebar.selectbox(
        "条件",
        ['%Kが%Dを上抜け（GC）', '%K < 20（売られすぎ）',
         '%K > 80（買われすぎ）', '%K範囲指定'])
    stoch_lo  = st.sidebar.slider("%K 下限", 0, 50, 20)
    stoch_hi  = st.sidebar.slider("%K 上限", 50, 100, 80)
else:
    stoch_k, stoch_d = 14, 3
    stoch_cond       = '%Kが%Dを上抜け（GC）'
    stoch_lo, stoch_hi = 20, 80

# ── MACD ──
# （パラメータ固定：12/26/9）

# ── ボリンジャーバンド ──
if use_bb:
    st.sidebar.markdown("#### 📐 ボリンジャーバンド")
    bb_period    = st.sidebar.slider("BB期間", 10, 30, 20)
    bb_threshold = st.sidebar.slider("%B 上限(買い条件)", 0, 100, 20)
else:
    bb_period, bb_threshold = 20, 20

# ── 出来高 ──
if use_vol:
    st.sidebar.markdown("#### 📦 出来高")
    vol_ratio = st.sidebar.slider("出来高比率(MA比)", 1.0, 5.0, 1.5, step=0.1)
else:
    vol_ratio = 1.5

params = {
    'ma_short':     ma_short,
    'ma_long':      ma_long,
    'ma_cond':      ma_cond,
    'rsi_period':   rsi_period,
    'rsi_lo':       rsi_lo,
    'rsi_hi':       rsi_hi,
    'stoch_k':      stoch_k,
    'stoch_d':      stoch_d,
    'stoch_cond':   stoch_cond,
    'stoch_lo':     stoch_lo,
    'stoch_hi':     stoch_hi,
    'bb_period':    bb_period,
    'bb_threshold': bb_threshold,
    'vol_ratio':    vol_ratio
}

# ── バックテスト設定 ──
st.sidebar.markdown("### 💴 バックテスト設定")
bt_cap = st.sidebar.number_input(
    "初期資金(円)", 100_000, 10_000_000, 1_000_000, step=100_000)

# =============================================
# メイン：データ読み込み
# =============================================
df_all = load_data()

if df_all.empty:
    st.error("❌ CSVファイルが見つかりません。stocks_OHLC_*.csv を同じフォルダに置いてください。")
    st.stop()

st.success(f"✅ データ読み込み完了：{len(df_all):,}行 / {df_all['Code'].nunique():,}銘柄")

# =============================================
# タブ構成
# =============================================
tab1, tab2 = st.tabs(["🔍 スクリーニング", "📊 3銘柄比較バックテスト"])

# =============================================
# TAB1：スクリーニング
# =============================================
with tab1:
    st.subheader("🔍 スクリーニング結果")

    if st.button("▶️ スクリーニング実行", type="primary"):
        codes   = df_all['Code'].unique()
        results = []

        prog = st.progress(0)
        for idx, code in enumerate(codes):
            df_s = df_all[df_all['Code'] == code].copy()
            d    = calc_indicators(df_s, params)
            ok, info = screen_stock(d, params, flags)
            if ok:
                row = df_s.iloc[-1]
                results.append({
                    'コード':   code,
                    '銘柄名':   row.get('Name',   ''),
                    'セクター': row.get('Sector', ''),
                    '市場':     row.get('Market', ''),
                    '終値':     info.get('Close', ''),
                    '変化率(%)': round(info.get('Change', 0), 2),
                    **{k: v for k, v in info.items()
                       if k not in ('Close', 'Change')}
                })
            prog.progress((idx + 1) / len(codes))

        if results:
            result_df = pd.DataFrame(results)
            st.success(f"✅ {len(result_df)} 銘柄がヒットしました")
            st.dataframe(result_df, use_container_width=True)
            st.download_button(
                "📥 結果をCSVダウンロード",
                result_df.to_csv(index=False, encoding='utf-8-sig'),
                "screening_result.csv"
            )
        else:
            st.warning("⚠️ 条件に合う銘柄が見つかりませんでした。条件を緩めてみてください。")

# =============================================
# TAB2：3銘柄比較バックテスト
# =============================================
with tab2:
    st.subheader("📊 3銘柄 比較バックテスト")

    # 銘柄リスト作成
    code_list = sorted(df_all['Code'].unique().tolist())

    # 銘柄名付きラベル
    name_map  = df_all.drop_duplicates('Code').set_index('Code')
    has_name  = 'Name' in name_map.columns

    def code_label(c):
        if has_name and c in name_map.index:
            return f"{c} {name_map.loc[c, 'Name']}"
        return c

    labels    = [code_label(c) for c in code_list]
    label_map = dict(zip(labels, code_list))

    # デフォルト選択（先頭3件）
    default_labels = labels[:3] if len(labels) >= 3 else labels

    st.markdown("#### 銘柄を3つ選択してください")
    col_sel1, col_sel2, col_sel3 = st.columns(3)

    with col_sel1:
        sel1 = st.selectbox("銘柄①", labels,
                            index=0, key='sel1')
    with col_sel2:
        sel2 = st.selectbox("銘柄②", labels,
                            index=min(1, len(labels)-1), key='sel2')
    with col_sel3:
        sel3 = st.selectbox("銘柄③", labels,
                            index=min(2, len(labels)-1), key='sel3')

    selected_codes = [label_map[sel1], label_map[sel2], label_map[sel3]]

    if st.button("▶️ バックテスト実行", type="primary"):

        # 3列レイアウト
        cols = st.columns(3)

        for col_idx, (col, code) in enumerate(zip(cols, selected_codes)):
            df_s = df_all[df_all['Code'] == code].copy()

            if df_s.empty:
                col.error(f"❌ {code} データなし")
                continue

            row_info = df_s.iloc[-1]
            name     = row_info.get('Name',   code)
            sector   = row_info.get('Sector', '')
            market   = row_info.get('Market', '')

            # インジケーター計算
            d = calc_indicators(df_s, params)

            # バックテスト実行
            trades_df, equity_df = run_backtest(df_s, params, flags, bt_cap)

            # サマリー
            summary = calc_summary(trades_df, equity_df, bt_cap)

            with col:
                # ── ヘッダー ──
                st.markdown(f"""
                <div style='background:#1e3a5f;padding:10px;border-radius:8px;
                            text-align:center;margin-bottom:10px'>
                    <h4 style='color:white;margin:0'>{code}</h4>
                    <p style='color:#aaddff;margin:0;font-size:13px'>{name}</p>
                    <p style='color:#88aacc;margin:0;font-size:11px'>
                        {sector} | {market}</p>
                </div>
                """, unsafe_allow_html=True)

                # ── ローソク足チャート ──
                fig_c = draw_chart(d, code, name, params, flags)
                st.plotly_chart(fig_c, use_container_width=True,
                                key=f'chart_{col_idx}')

                # ── 損益曲線 ──
                fig_e = draw_equity(equity_df, trades_df, code, name)
                st.plotly_chart(fig_e, use_container_width=True,
                                key=f'equity_{col_idx}')

                # ── サマリーカード ──
                ret_color = 'red' if summary['リターン(%)'] >= 0 else 'blue'
                st.markdown(f"""
                <div style='background:#f8f9fa;padding:10px;border-radius:8px;
                            border-left:4px solid {ret_color}'>
                    <table style='width:100%;font-size:13px'>
                        <tr><td>📊 トレード数</td>
                            <td align='right'><b>{summary['総トレード数']}</b></td></tr>
                        <tr><td>🎯 勝率</td>
                            <td align='right'><b>{summary['勝率(%)']}%</b></td></tr>
                        <tr><td>💰 総損益</td>
                            <td align='right'><b style='color:{ret_color}'>
                            ¥{summary['総損益(円)']:,}</b></td></tr>
                        <tr><td>📈 リターン</td>
                            <td align='right'><b style='color:{ret_color}'>
                            {summary['リターン(%)']}%</b></td></tr>
                        <tr><td>📉 最大DD</td>
                            <td align='right'><b>{summary['最大DD(%)']}%</b></td></tr>
                        <tr><td>📅 平均保有</td>
                            <td align='right'><b>{summary['平均保有日数']}日</b></td></tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                # ── トレード詳細 ──
                if len(trades_df) > 0:
                    with st.expander("📋 トレード詳細"):
                        st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("トレードなし")