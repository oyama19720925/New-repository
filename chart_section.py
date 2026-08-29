# chart_section.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def plot_stock_chart(df: pd.DataFrame, code: str, name: str, color: str = "#00bfff") -> go.Figure:
    """
    ローソク足 + 移動平均 + 出来高チャートを生成
    """
    df = df.copy().sort_values('Date')

    # 移動平均
    df['MA5']  = df['Close'].rolling(5).mean()
    df['MA25'] = df['Close'].rolling(25).mean()
    df['MA75'] = df['Close'].rolling(75).mean()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03
    )

    # ── ローソク足 ──
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='価格',
        increasing_line_color='#ff4444',
        decreasing_line_color='#00bfff',
    ), row=1, col=1)

    # ── 移動平均線 ──
    for ma, col_ma, width in [
        ('MA5',  '#ffff00', 1),
        ('MA25', '#ff8800', 1.5),
        ('MA75', '#ff00ff', 2),
    ]:
        if ma in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df[ma],
                mode='lines', name=ma,
                line=dict(color=col_ma, width=width)
            ), row=1, col=1)

    # ── 出来高 ──
    colors_vol = [
        '#ff4444' if c >= o else '#00bfff'
        for c, o in zip(df['Close'], df['Open'])
    ]
    fig.add_trace(go.Bar(
        x=df['Date'],
        y=df['Volume'],
        name='出来高',
        marker_color=colors_vol,
        opacity=0.7
    ), row=2, col=1)

    fig.update_layout(
        title=dict(
            text=f"<b>{code} {name}</b>",
            font=dict(size=16, color=color)
        ),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1a1a2e',
        font=dict(color='white'),
        height=500,
        margin=dict(l=40, r=40, t=60, b=20),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='right', x=1
        ),
        showlegend=True,
    )

    fig.update_xaxes(
        gridcolor='#333',
        showgrid=True
    )
    fig.update_yaxes(
        gridcolor='#333',
        showgrid=True
    )

    return fig