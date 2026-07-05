"""自选股：增删查（watchlist 表）。看板 board() 见后续任务。"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..data import store


def add(code: str) -> None:
    code = str(code)
    # 检查是否已存在，幂等
    if store.has_table("watchlist"):
        with store.connect() as con:
            r = con.execute("SELECT 1 FROM watchlist WHERE code = ?", [code]).fetchone()
            if r:  # 已存在则直接返回
                return
    store.save("watchlist", pd.DataFrame([{
        "code": code, "added_ts": datetime.now().isoformat(timespec="seconds")}]))


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
    df = store.query("SELECT code FROM watchlist ORDER BY added_ts, rowid")
    return [str(c) for c in df["code"].tolist()]
