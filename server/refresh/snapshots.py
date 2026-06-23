"""盘中快照刷新任务：拉第三方现价/板块/指数 → 落 DuckDB。只在后台运行。"""
from __future__ import annotations

from datetime import datetime

from aquant.data import store
from aquant.data.sources import akshare_source as src


def refresh_quotes(fetch=None) -> int:
    """全市场现价快照入库 quote_snapshot，返回写入行数。"""
    fetch = fetch or src.spot_snapshot
    df = fetch()
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["ts"] = datetime.now().isoformat(timespec="seconds")
    return store.save("quote_snapshot", df)
