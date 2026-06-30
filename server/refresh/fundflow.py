"""资金流刷新任务：行业板块资金、全市场个股资金 → 落 DuckDB。后台运行。"""
from __future__ import annotations

from datetime import date

from aquant.data import store
from aquant.data.sources import akshare_source as src


def refresh_sector_fund_flow(fetch=None) -> int:
    """行业板块资金流入库 sector_fund_flow（按 [sector,date] upsert，当日覆盖）。"""
    fetch = fetch or src.sector_fund_flow
    df = fetch()
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["date"] = date.today().isoformat()
    return store.save("sector_fund_flow", df)


def refresh_fund_flow(fetch=None) -> int:
    """全市场个股资金流入库 fund_flow（按 [code,date] upsert，当日覆盖）。"""
    fetch = fetch or src.fund_flow_rank
    df = fetch()
    if df is None or df.empty:
        return 0
    keep = [c for c in ("code", "name", "close", "pct_chg", "main_net", "main_net_pct") if c in df.columns]
    df = df[keep].copy()
    df["date"] = date.today().isoformat()
    return store.save("fund_flow", df)
