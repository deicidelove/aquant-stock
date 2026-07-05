"""自选股：增删查（watchlist 表）。看板 board() 见后续任务。"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..data import store
from .. import research
from . import holdings


def add(code: str) -> None:
    code = str(code)
    # 检查是否已存在，幂等
    if store.has_table("watchlist"):
        with store.connect() as con:
            r = con.execute("SELECT 1 FROM watchlist WHERE code = ?", [code]).fetchone()
            if r:  # 已存在则直接返回
                return
    # 微秒精度时间戳：保证 ORDER BY added_ts 稳定复现插入序，不依赖 DuckDB rowid
    store.save("watchlist", pd.DataFrame([{
        "code": code, "added_ts": datetime.now().isoformat()}]))


def remove(code: str) -> int:
    if not store.has_table("watchlist"):
        return 0
    with store.connect() as con:
        before = con.execute("SELECT count(*) FROM watchlist WHERE code = ?", [code]).fetchone()[0]
        con.execute("DELETE FROM watchlist WHERE code = ?", [code])
    return int(before)


def list_codes() -> list[str]:
    if not store.has_table("watchlist"):
        return []
    df = store.query("SELECT code FROM watchlist ORDER BY added_ts")
    return [str(c) for c in df["code"].tolist()]


def board(kline_n: int = 30) -> list[dict]:
    held = {c for c, p in holdings._positions().items() if p["shares"] > 1e-9}
    codes = list(dict.fromkeys(list_codes() + sorted(held)))  # 自选在前，持仓补齐，去重
    out = []
    for code in codes:
        df = store.load_daily(code)
        if df.empty:
            continue
        last_row = df.iloc[-1]
        last_price = holdings._latest_price(code)
        pct_chg = float(last_row["pct_chg"]) if "pct_chg" in df.columns and pd.notna(last_row["pct_chg"]) else None
        kline = [{"date": str(r["date"]), "close": float(r["close"])}
                 for _, r in df.tail(kline_n).iterrows()]
        dec = research.decision(code, offline=True) or {}
        out.append({
            "code": code, "name": holdings._name_of(code),
            "last_price": last_price, "pct_chg": pct_chg, "kline": kline,
            "signal": dec.get("signal", ""), "one_liner": dec.get("one_liner", ""),
            "battle_plan": dec.get("battle_plan", {}), "risk_level": dec.get("risk_level", ""),
            "alerts": holdings.sell_alerts(code, last_price, dec=dec or None),
        })
    return out
