"""宏观盘面：市场情绪、大盘资金趋势、多指数。只读 DuckDB，无第三方联网。"""
from __future__ import annotations

import pandas as pd

from . import market
from .data import store

_INDEX_DEFAULTS = ["sh000300", "sh000001", "sz399006"]


def _latest_rows() -> pd.DataFrame:
    """每只股票最新一日的 close/pct_chg/amount。"""
    if not store.has_table("daily_bar"):
        return pd.DataFrame()
    return store.query(
        "SELECT code, pct_chg, amount FROM ("
        "  SELECT code, pct_chg, amount, row_number() OVER "
        "    (PARTITION BY code ORDER BY date DESC) rn FROM daily_bar) t WHERE rn = 1")


def sentiment() -> dict:
    b = market.breadth()
    df = _latest_rows()
    limit_down = int((df["pct_chg"] <= -9.8).sum()) if not df.empty else 0
    amount = float(df["amount"].sum()) if not df.empty and "amount" in df else 0.0
    up, down = b.get("up", 0), b.get("down", 0)
    limit_up = b.get("limit_up", 0)
    total = max(b.get("total", 0), 1)
    # 温度 0~100：上涨占比为主 + 涨停溢价 − 跌停惩罚
    up_ratio = up / total
    score = max(0.0, min(100.0, up_ratio * 100 + (limit_up - limit_down) / total * 200))
    label = ("过热" if score >= 80 else "偏热" if score >= 60 else
             "中性" if score >= 40 else "偏冷" if score >= 20 else "冰点")
    return {"up": up, "down": down, "limit_up": limit_up, "limit_down": limit_down,
            "amount": round(amount, 2), "score": round(score, 1), "label": label}


def market_fund_trend(days: int = 10) -> dict:
    if not store.has_table("fund_flow"):
        return {"today": 0.0, "series": []}
    df = store.query("SELECT date, sum(main_net) net FROM fund_flow GROUP BY date ORDER BY date")
    if df.empty:
        return {"today": 0.0, "series": []}
    df["net"] = (df["net"] / 1e8).round(2)
    tail = df.tail(days)
    series = [{"date": str(r["date"]), "net": float(r["net"])} for _, r in tail.iterrows()]
    return {"today": float(tail["net"].iloc[-1]), "series": series}


def indices(codes: list[str] | None = None) -> list[dict]:
    out = []
    for c in (codes or _INDEX_DEFAULTS):
        t = market.index_trend(c)
        if t:
            out.append(t)
    return out
