"""专业K线数据：K线(OHLC+量) + 均线(MA5/10/20/60) + MACD(DIF/DEA/hist)。只读库。"""
from __future__ import annotations

import pandas as pd

from .data import store


def _col(series: pd.Series) -> list:
    return [round(float(v), 2) if pd.notna(v) else None for v in series]


def stock_chart(code: str, n: int = 250) -> dict:
    empty = {"code": code, "bars": [],
             "ma": {"ma5": [], "ma10": [], "ma20": [], "ma60": []},
             "macd": {"dif": [], "dea": [], "hist": []}}
    if not store.has_table("daily_bar"):
        return empty
    df = store.query(
        "SELECT date, open, high, low, close, volume FROM daily_bar WHERE code = ? ORDER BY date", [code])
    if df.empty:
        return empty
    c = df["close"]
    for w in (5, 10, 20, 60):
        df[f"ma{w}"] = c.rolling(w).mean()
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = (dif - dea) * 2
    df["dif"], df["dea"], df["hist"] = dif, dea, hist
    t = df.tail(n)
    bars = [{"date": str(r["date"]), "open": round(float(r["open"]), 2),
             "high": round(float(r["high"]), 2), "low": round(float(r["low"]), 2),
             "close": round(float(r["close"]), 2), "volume": int(r["volume"])}
            for _, r in t.iterrows()]
    return {
        "code": code, "bars": bars,
        "ma": {"ma5": _col(t["ma5"]), "ma10": _col(t["ma10"]), "ma20": _col(t["ma20"]), "ma60": _col(t["ma60"])},
        "macd": {"dif": _col(t["dif"]), "dea": _col(t["dea"]), "hist": _col(t["hist"])},
    }
