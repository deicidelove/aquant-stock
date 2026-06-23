"""择时信号：生成买卖点。

每个信号函数接收单只股票日线（按日期升序），返回与之对齐的持仓信号 Series：
1=持有/买入，0=空仓/卖出。供回测层与看盘信号面板共用。

这是“什么时候买卖”的核心。信号只用截至当日的信息，无未来函数。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ma_cross(df: pd.DataFrame, fast: int = 5, slow: int = 20) -> pd.Series:
    """均线金叉持有 / 死叉空仓。fast 上穿 slow 买入。"""
    c = df["close"]
    mf, ms = c.rolling(fast).mean(), c.rolling(slow).mean()
    return (mf > ms).astype(float)


def breakout(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """唐奇安通道突破：创 window 日新高买入，跌破 window 日新低卖出。"""
    high_n = df["high"].rolling(window).max()
    low_n = df["low"].rolling(window).min()
    sig = pd.Series(np.nan, index=df.index)
    sig[df["close"] >= high_n.shift(1)] = 1.0
    sig[df["close"] <= low_n.shift(1)] = 0.0
    return sig.ffill().fillna(0)


def macd_signal(df: pd.DataFrame) -> pd.Series:
    """MACD 柱由负转正买入，由正转负卖出。"""
    c = df["close"]
    dif = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = dif - dea
    return (hist > 0).astype(float)


def trend_filter(df: pd.DataFrame, ma: int = 60) -> pd.Series:
    """趋势过滤：价在 MA60 之上才允许持仓（大盘/个股中期向上）。"""
    return (df["close"] > df["close"].rolling(ma).mean()).astype(float)


SIGNALS = {
    "ma_cross": ma_cross,
    "breakout": breakout,
    "macd": macd_signal,
    "trend_filter": trend_filter,
}


def combine(df: pd.DataFrame, names: list[str], mode: str = "and") -> pd.Series:
    """组合多个信号。mode='and' 全部满足才持有；'or' 任一满足即持有。"""
    sigs = [SIGNALS[n](df) for n in names]
    stacked = pd.concat(sigs, axis=1).fillna(0)
    return (stacked.min(axis=1) if mode == "and" else stacked.max(axis=1)).astype(float)


def latest_action(df: pd.DataFrame, name: str = "ma_cross") -> dict:
    """给出最新一日的操作建议（买入/持有/卖出/空仓）及触发日期。"""
    sig = SIGNALS[name](df).fillna(0)
    if len(sig) < 2:
        return {"action": "数据不足", "date": None}
    today, prev = sig.iloc[-1], sig.iloc[-2]
    d = df["date"].iloc[-1]
    if prev == 0 and today == 1:
        return {"action": "买入", "date": d}
    if prev == 1 and today == 0:
        return {"action": "卖出", "date": d}
    return {"action": "持有" if today == 1 else "空仓", "date": d}
