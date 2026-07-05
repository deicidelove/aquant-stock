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


def sector_fund_rank(top: int = 20) -> dict:  # noqa: ARG001 预留前端切分用
    if not store.has_table("sector_fund_flow"):
        return {"as_of": None, "rows": []}
    as_of = store.query("SELECT max(date) d FROM sector_fund_flow")["d"].iloc[0]
    if as_of is None:
        return {"as_of": None, "rows": []}
    df = store.query("SELECT sector,pct_chg,main_net,main_net_pct,leader FROM sector_fund_flow "
                     "WHERE date = ? ORDER BY main_net DESC", [as_of])
    return {"as_of": str(as_of), "rows": df.to_dict(orient="records")}


def abnormal_fund(scope: str = "stock", n: int = 20, z: float = 2.0, top: int = 20) -> dict:
    table, key = ("fund_flow", "code") if scope == "stock" else ("sector_fund_flow", "sector")
    if not store.has_table(table):
        return {"scope": scope, "rows": []}
    df = store.query(f"SELECT {key} k, date, main_net FROM {table} ORDER BY {key}, date")
    if df.empty:
        return {"scope": scope, "rows": []}
    out = []
    for k, g in df.groupby("k", sort=False):
        vals = g["main_net"].astype(float).tolist()
        if len(vals) < 3:
            continue
        latest = vals[-1]
        hist = vals[max(0, len(vals) - 1 - n):-1]  # 除最新外近 n 个
        if len(hist) < 2:
            continue
        s = pd.Series(hist)
        mean, std = float(s.mean()), float(s.std(ddof=0))
        if std <= 0:
            continue
        zz = (latest - mean) / std
        if abs(zz) >= z:
            out.append({"key": str(k), "latest": round(latest, 2), "mean": round(mean, 2),
                        "std": round(std, 2), "z": round(zz, 2)})
    out.sort(key=lambda x: abs(x["z"]), reverse=True)
    return {"scope": scope, "rows": out[:top]}


def regime() -> dict:
    return market.regime()


def index_series(code: str = "sh000300", n: int = 120) -> dict:
    if not store.has_table("index_daily"):
        return {"code": code, "points": []}
    df = store.query("SELECT date, close FROM index_daily WHERE code = ? ORDER BY date", [code])
    if df.empty:
        return {"code": code, "points": []}
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    tail = df.tail(n)
    points = [{"date": str(r["date"]), "close": round(float(r["close"]), 2),
               "ma20": round(float(r["ma20"]), 2) if pd.notna(r["ma20"]) else None,
               "ma60": round(float(r["ma60"]), 2) if pd.notna(r["ma60"]) else None}
              for _, r in tail.iterrows()]
    return {"code": code, "points": points}


def amount_trend(days: int = 20) -> dict:
    if not store.has_table("daily_bar"):
        return {"series": []}
    df = store.query("SELECT date, sum(amount) amt FROM daily_bar GROUP BY date ORDER BY date")
    if df.empty:
        return {"series": []}
    tail = df.tail(days)
    series = [{"date": str(r["date"]), "amount": round(float(r["amt"]) / 1e8, 2)}
              for _, r in tail.iterrows()]
    return {"series": series}
