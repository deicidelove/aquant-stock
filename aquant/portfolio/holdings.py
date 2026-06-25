"""我的持仓：从手动交易流水 trades 聚合当前持仓与盈亏。

纯领域逻辑（只读/写 DuckDB，无第三方联网）。加权平均成本法：买入摊薄成本，
卖出按当时加权成本结转已实现盈亏、不改成本。最新价优先盘中快照、回退收盘。
"""
from __future__ import annotations

import pandas as pd

from ..data import store

_EPS = 1e-9


def record_trade(date: str, code: str, side: str, shares: float, price: float, note: str = "") -> int:
    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")
    cur = store.query("SELECT max(tid) m FROM trades") if store.has_table("trades") else pd.DataFrame()
    tid = int((cur["m"].iloc[0] if not cur.empty and pd.notna(cur["m"].iloc[0]) else 0)) + 1
    store.save("trades", pd.DataFrame([{
        "tid": tid, "date": date, "code": str(code), "side": side,
        "shares": float(shares), "price": float(price), "note": note}]))
    return tid


def list_trades() -> pd.DataFrame:
    if not store.has_table("trades"):
        return pd.DataFrame()
    return store.query("SELECT * FROM trades ORDER BY tid")


def delete_trade(tid: int) -> int:
    if not store.has_table("trades"):
        return 0
    with store.connect() as con:
        before = con.execute("SELECT count(*) FROM trades WHERE tid = ?", [tid]).fetchone()[0]
        con.execute("DELETE FROM trades WHERE tid = ?", [tid])
    return int(before)


def _latest_price(code: str) -> float | None:
    if store.has_table("quote_snapshot"):
        q = store.query(
            "SELECT close FROM quote_snapshot WHERE code = ? "
            "AND ts = (SELECT max(ts) FROM quote_snapshot WHERE code = ?)", [code, code])
        if not q.empty and pd.notna(q["close"].iloc[0]):
            return float(q["close"].iloc[0])
    d = store.load_daily(code)
    if not d.empty:
        return float(d["close"].iloc[-1])
    return None


def _name_of(code: str) -> str:
    if store.has_table("stock_basic"):
        r = store.query("SELECT name FROM stock_basic WHERE code = ?", [code])
        if not r.empty:
            return str(r["name"].iloc[0])
    return ""


def _positions() -> dict[str, dict]:
    """逐 code 按时间回放，得每只 {shares, avg_cost, realized}。"""
    df = list_trades()
    acc: dict[str, dict] = {}
    if df.empty:
        return acc
    for _, t in df.sort_values(["date", "tid"]).iterrows():
        p = acc.setdefault(t["code"], {"shares": 0.0, "avg_cost": 0.0, "realized": 0.0})
        sh, pr = float(t["shares"]), float(t["price"])
        if t["side"] == "buy":
            tot = p["shares"] + sh
            p["avg_cost"] = (p["shares"] * p["avg_cost"] + sh * pr) / tot if tot > _EPS else 0.0
            p["shares"] = tot
        else:  # sell
            p["realized"] += (pr - p["avg_cost"]) * sh
            p["shares"] -= sh
    return acc


def holdings() -> list[dict]:
    out = []
    for code, p in _positions().items():
        if p["shares"] <= _EPS:
            continue
        last = _latest_price(code)
        mv = (last or 0.0) * p["shares"]
        unreal = (last - p["avg_cost"]) * p["shares"] if last is not None else 0.0
        unreal_pct = (last / p["avg_cost"] - 1) * 100 if last is not None and p["avg_cost"] > _EPS else 0.0
        out.append({
            "code": code, "name": _name_of(code), "shares": round(p["shares"], 4),
            "avg_cost": round(p["avg_cost"], 4), "last_price": last,
            "market_value": round(mv, 2), "unrealized": round(unreal, 2),
            "unrealized_pct": round(unreal_pct, 2)})
    return out


def sell_alerts(code: str, last_price: float | None, dec: dict | None = None) -> list[str]:
    if last_price is None:
        return []
    if dec is None:
        from .. import research
        dec = research.decision(code, offline=True)
    if not dec:
        return []
    plan = dec.get("battle_plan", {})
    alerts = []
    stop, target = plan.get("stop_loss"), plan.get("take_profit")
    if stop is not None and last_price <= stop:
        alerts.append("跌破止损")
    if target is not None and last_price >= target:
        alerts.append("到压力位")
    if str(dec.get("signal", "")).startswith("回避"):
        alerts.append("信号转空")
    return alerts


def holdings_view() -> list[dict]:
    out = []
    for h in holdings():
        h = dict(h)
        h["alerts"] = sell_alerts(h["code"], h["last_price"])
        out.append(h)
    return out


def pnl_summary() -> dict:
    pos = _positions()
    realized = sum(p["realized"] for p in pos.values())
    unrealized = sum(h["unrealized"] for h in holdings())
    return {"realized": round(realized, 2), "unrealized": round(unrealized, 2),
            "total": round(realized + unrealized, 2)}
