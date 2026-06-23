"""数据接入：拉取 → 落库。对外只暴露少量编排函数。"""
from __future__ import annotations

import pandas as pd

from . import store
from .sources import akshare_source as src


def ingest_basic() -> int:
    """更新股票列表 stock_basic。"""
    return store.save("stock_basic", src.stock_list())


def ingest_daily(code: str, start: str | None = None, incremental: bool = True) -> int:
    """拉取单只股票日线并落库。

    incremental=True 时从已有最大日期之后续拉，避免重复全量。
    """
    if incremental and start is None:
        last = store.max_date("daily_bar", code)
        if last:
            start = (pd.to_datetime(last) + pd.Timedelta(days=1)).strftime("%Y%m%d")
    df = src.daily_bar(code, start=start)
    return store.save("daily_bar", df)


def ingest_daily_many(codes: list[str], start: str | None = None,
                      incremental: bool = True) -> pd.DataFrame:
    """批量接入日线，单只失败不阻断整批。返回每只结果。"""
    rows = []
    for c in codes:
        try:
            n = ingest_daily(c, start=start, incremental=incremental)
            rows.append({"code": c, "rows": n, "ok": True, "err": ""})
        except Exception as e:
            rows.append({"code": c, "rows": 0, "ok": False, "err": str(e)[:120]})
    return pd.DataFrame(rows)


def ingest_fund_flow() -> int:
    """主力资金净流入/流出排行快照（当日，各取前200），落库到 fund_flow。

    用直连 Top-N 接口（一次请求，稳），不再爬 53 页全市场，避免断流。
    """
    inflow = src.fund_flow_top(200, "in")
    outflow = src.fund_flow_top(200, "out")
    df = pd.concat([inflow, outflow]).drop_duplicates(subset="code")
    if df.empty:
        return 0
    df["date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    return store.save("fund_flow", df)


def ingest_index(index_code: str = "sh000300") -> int:
    """指数日线入库（沪深300/中证500 等）。"""
    return store.save("index_daily", src.index_daily(index_code))


def ingest_valuation() -> int:
    """全市场估值快照（PE/PB/市值/换手）入库到 fundamental（带当日日期）。"""
    from .sources import fundamental as fund
    df = fund.valuation_snapshot()
    if df.empty:
        return 0
    df["date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    return store.save("fundamental", df)


def ingest_sectors() -> int:
    """行业板块当日快照，落库到 sector_daily（带当日日期）。"""
    df = src.industry_snapshot()
    if df.empty:
        return 0
    df["date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    return store.save("sector_daily", df)
