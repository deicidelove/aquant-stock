"""涨停梯队 / 北向 刷新任务：抓当日涨停池 + 北向汇总 → 落 DuckDB。后台运行。"""
from __future__ import annotations

from datetime import date

from aquant.data import store
from aquant.data.sources import akshare_source as src


def refresh_limit_pool() -> int:
    """当日涨停池入库 limit_pool（按 [code,date] upsert）。"""
    today = date.today()
    df = src.limit_pool(today.strftime("%Y%m%d"))
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["date"] = today.isoformat()
    return store.save("limit_pool", df)


def refresh_north() -> int:
    """北向汇总入库 north_flow（按 [date,market] upsert）。"""
    df = src.north_summary()
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["date"] = date.today().isoformat()
    return store.save("north_flow", df[["date", "market", "net"]])
