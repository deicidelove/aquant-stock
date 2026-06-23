"""模拟盘账户：现金 + 持仓 + 交易流水，落 DuckDB。

闭环的"实操"环节：按推荐建仓/换仓 → 每日盯市记净值 → 供绩效分析与反馈优化。
所有成交按 daily_bar 收盘价、含双边手续费，无撮合/滑点（研究级模拟）。
"""
from __future__ import annotations

import pandas as pd

from ..data import store

INIT_CAPITAL = 1_000_000.0
FEE = 0.0013  # 双边总费率（买卖各半）

# 交易流水（append-only）与每日净值快照
store.TABLE_KEYS.setdefault("paper_trade", ["tid"])
store.TABLE_KEYS.setdefault("paper_nav", ["date"])
store.TABLE_KEYS.setdefault("paper_meta", ["key"])


def reset(capital: float = INIT_CAPITAL) -> None:
    """清空模拟盘，重置初始资金。"""
    with store.connect() as con:
        for t in ("paper_trade", "paper_nav"):
            con.execute(f'DROP TABLE IF EXISTS "{t}"')
    store.save("paper_meta", pd.DataFrame([{"key": "init_capital", "val": float(capital)}]))
    store.save("paper_meta", pd.DataFrame([{"key": "cash", "val": float(capital)}]))


def _meta(key: str, default: float = 0.0) -> float:
    if not store.has_table("paper_meta"):
        return default
    r = store.query("SELECT val FROM paper_meta WHERE key = ?", [key])
    return float(r["val"].iloc[0]) if not r.empty else default


def _set_meta(key: str, val: float) -> None:
    store.save("paper_meta", pd.DataFrame([{"key": key, "val": float(val)}]))


def cash() -> float:
    return _meta("cash", INIT_CAPITAL)


def _next_tid() -> int:
    if not store.has_table("paper_trade"):
        return 1
    r = store.query("SELECT max(tid) m FROM paper_trade")
    return int((r["m"].iloc[0] or 0)) + 1


def positions() -> pd.DataFrame:
    """当前持仓：code, shares, avg_cost（由流水聚合）。"""
    if not store.has_table("paper_trade"):
        return pd.DataFrame(columns=["code", "shares", "avg_cost"])
    tr = store.query("SELECT * FROM paper_trade ORDER BY tid")
    pos: dict[str, dict] = {}
    for r in tr.itertuples(index=False):
        p = pos.setdefault(r.code, {"shares": 0.0, "cost": 0.0})
        if r.side == "buy":
            p["cost"] += r.shares * r.price
            p["shares"] += r.shares
        else:
            # 卖出按比例减少成本
            if p["shares"] > 0:
                p["cost"] *= max(0.0, (p["shares"] - r.shares)) / p["shares"]
            p["shares"] -= r.shares
    rows = [{"code": c, "shares": round(v["shares"], 2),
             "avg_cost": round(v["cost"] / v["shares"], 3) if v["shares"] > 0 else 0.0}
            for c, v in pos.items() if v["shares"] > 1e-6]
    return pd.DataFrame(rows)


def _record(date: str, code: str, side: str, shares: float, price: float, note: str = "") -> None:
    amount = shares * price
    fee = amount * (FEE / 2)
    store.save("paper_trade", pd.DataFrame([{
        "tid": _next_tid(), "date": date, "code": code, "side": side,
        "shares": round(shares, 2), "price": round(price, 3),
        "amount": round(amount, 2), "fee": round(fee, 2), "note": note}]))
    _set_meta("cash", cash() + (amount - fee if side == "sell" else -(amount + fee)))


def closes_on(date: str, codes: list[str]) -> dict[str, float]:
    """取一批股票在 date（含）之前最近一个交易日的收盘价。"""
    if not codes:
        return {}
    ph = ",".join("?" * len(codes))
    df = store.query(
        f"SELECT code, close FROM ("
        f"  SELECT code, close, row_number() OVER (PARTITION BY code ORDER BY date DESC) rn"
        f"  FROM daily_bar WHERE date <= ? AND code IN ({ph})) t WHERE rn = 1",
        [date] + codes)
    return dict(zip(df["code"], df["close"]))


def total_value(date: str) -> float:
    pos = positions()
    if pos.empty:
        return cash()
    px = closes_on(date, pos["code"].tolist())
    holdings = sum(r.shares * px.get(r.code, r.avg_cost) for r in pos.itertuples(index=False))
    return cash() + holdings


def mark(date: str) -> dict:
    """盯市：记录当日净值快照。"""
    pos = positions()
    px = closes_on(date, pos["code"].tolist()) if not pos.empty else {}
    holdings = sum(r.shares * px.get(r.code, r.avg_cost) for r in pos.itertuples(index=False))
    total = cash() + holdings
    store.save("paper_nav", pd.DataFrame([{
        "date": date, "cash": round(cash(), 2),
        "holdings": round(holdings, 2), "total": round(total, 2)}]))
    return {"date": date, "cash": cash(), "holdings": holdings, "total": total}


def rebalance(date: str, target_codes: list[str], note: str = "rebalance") -> dict:
    """调仓到等权目标组合：卖出不在目标内的，按等权买入目标。"""
    pos = positions()
    cur = set(pos["code"]) if not pos.empty else set()
    target = set(target_codes)
    px = closes_on(date, list(cur | target))

    # 1) 卖出不在目标里的
    sold = 0
    for r in pos.itertuples(index=False):
        if r.code not in target and r.code in px:
            _record(date, r.code, "sell", r.shares, px[r.code], note)
            sold += 1

    # 2) 等权买入目标（用调仓后总资产）
    tv = total_value(date)
    buyable = [c for c in target_codes if c in px and px[c] > 0]
    if not buyable:
        m = mark(date)
        return {"date": date, "sold": sold, "bought": 0, **m}
    per = (tv * 0.99) / len(buyable)  # 留 1% 现金缓冲
    pos2 = positions()
    held = dict(zip(pos2["code"], pos2["shares"])) if not pos2.empty else {}
    bought = 0
    for c in buyable:
        tgt_shares = (per / px[c]) // 100 * 100  # 整百股
        delta = tgt_shares - held.get(c, 0)
        if delta >= 100:
            _record(date, c, "buy", delta, px[c], note)
            bought += 1
        elif delta <= -100:
            _record(date, c, "sell", -delta, px[c], note)
    m = mark(date)
    return {"date": date, "sold": sold, "bought": bought, **m}


def nav_series() -> pd.DataFrame:
    if not store.has_table("paper_nav"):
        return pd.DataFrame(columns=["date", "total"])
    return store.query("SELECT * FROM paper_nav ORDER BY date")
