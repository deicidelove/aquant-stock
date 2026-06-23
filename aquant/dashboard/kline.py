"""K 线图绘制（Plotly），从本地仓库读数据出图。

可独立用于快速查看个股走势，也供看盘 Dashboard 复用。
"""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go

from .. import config
from ..data import store


def kline_figure(code: str, last_n: int | None = 250, ma=(5, 20, 60)) -> go.Figure:
    """构建单只股票的 K 线 + 均线 + 成交量图。"""
    df = store.load_daily(code)
    if df.empty:
        raise ValueError(f"本地无 {code} 数据，请先 ingest。")
    if last_n:
        df = df.tail(last_n)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="K线",
        increasing_line_color="#e63946", decreasing_line_color="#2a9d8f",
    ))
    for w in ma:
        if len(df) >= w:
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["close"].rolling(w).mean(),
                mode="lines", name=f"MA{w}", line=dict(width=1)))
    fig.update_layout(
        title=f"{code} 日K（最近 {len(df)} 根，前复权）",
        xaxis_rangeslider_visible=False, template="plotly_white",
        height=600, legend=dict(orientation="h", y=1.02, x=0))
    return fig


def mini_figure(code: str, name: str = "", last_n: int = 120) -> go.Figure:
    """迷你走势图（收盘价+MA20，极简坐标），用于网格小图速览。"""
    df = store.load_daily(code)
    if df.empty:
        return go.Figure()
    df = df.tail(last_n)
    chg = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
    color = "#e63946" if chg >= 0 else "#2a9d8f"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines",
                             line=dict(color=color, width=1.5)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["close"].rolling(20).mean(),
                             mode="lines", line=dict(color="#888", width=0.8, dash="dot")))
    fig.update_layout(
        title=dict(text=f"{code} {name} {chg:+.1f}%", font=dict(size=11)),
        showlegend=False, margin=dict(l=4, r=4, t=22, b=4), height=150,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        template="plotly_white")
    return fig


def save_png(code: str, last_n: int | None = 250, out: Path | None = None) -> Path:
    """导出 K 线 PNG（需要 kaleido）。失败则回退导出 HTML。"""
    fig = kline_figure(code, last_n=last_n)
    out = out or (config.DATA_DIR / f"kline_{code}.png")
    try:
        fig.write_image(str(out))
    except Exception:
        out = out.with_suffix(".html")
        fig.write_html(str(out))
    return out
