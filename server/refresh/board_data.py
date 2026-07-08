"""涨停梯队 / 北向 / 融资融券 / 大宗 刷新任务 → 落 DuckDB。后台运行。"""
from __future__ import annotations

from datetime import date, timedelta

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


def refresh_margin() -> int:
    """两市融资融券入库 margin_balance。SSE 取近~10交易日区间，SZSE 取最新日。"""
    written = 0
    end = date.today()
    start = end - timedelta(days=15)
    try:
        sse = src.margin_sse(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
        if sse is not None and not sse.empty:
            sse = sse.dropna(subset=["date"]).copy()
            sse["market"] = "sh"
            written += store.save("margin_balance", sse[["date", "market", "fin_balance", "total_balance"]])
    except Exception:  # noqa: BLE001 单市场失败不影响另一个
        pass
    try:
        # SZSE 最新交易日：用 SSE 最新日或今天
        d = end
        for _ in range(7):
            sz = src.margin_szse(d.strftime("%Y%m%d"))
            if sz is not None and not sz.empty and sz["total_balance"].iloc[0]:
                sz = sz.copy()
                sz["market"] = "sz"
                written += store.save("margin_balance", sz[["date", "market", "fin_balance", "total_balance"]])
                break
            d -= timedelta(days=1)
    except Exception:  # noqa: BLE001
        pass
    return written


def refresh_block_trade(days: int = 10) -> int:
    """大宗交易统计入库 block_trade（取近 days 日）。"""
    df = src.block_trade_stat()
    if df is None or df.empty:
        return 0
    df = df.dropna(subset=["date"]).sort_values("date").tail(days)
    return store.save("block_trade", df)
