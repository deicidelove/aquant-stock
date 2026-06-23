"""推荐快照入库。

台账只存「当日推荐了什么」的快照（不存前向收益——那是 evaluate 的纯函数计算）：
    (as_of, code, name, rank, score, action, signal, entry_close)
主键 (as_of, code)，经 store 幂等 upsert，重复跑同日不产生重复行。

- snapshot():    把当日 research.daily_picks 的推荐写入 picks_log（接入 run_daily）。
- reconstruct(): 用历史数据按周频回放过去的当日推荐，冷启动台账，上线即有样本。
"""
from __future__ import annotations

import pandas as pd

from ..data import store
from ..select import scorer
from .. import research

TABLE = "picks_log"


def snapshot(as_of: str | None = None, top: int = 30, signal: str = "ma_cross",
             drop_boards=None) -> int:
    """把当日推荐写入 picks_log，返回写入行数。

    as_of 缺省=库内最新交易日（实时口径）。复用 research.daily_picks，故 action /
    择时信号与每日决策清单完全一致。drop_boards 与当日决策口径保持一致。
    """
    picks = research.daily_picks(top=top, signal=signal, as_of=as_of,
                                 require_uptrend=False, drop_boards=drop_boards)
    if picks.empty:
        return 0
    day = as_of or store.query("SELECT max(date) d FROM daily_bar")["d"].iloc[0]
    rows = []
    for rank, r in enumerate(picks.itertuples(index=False), start=1):
        rows.append({
            "as_of": day,
            "code": r.code,
            "name": getattr(r, "name", ""),
            "rank": rank,
            "score": float(r.score),
            "action": getattr(r, "action", ""),
            "signal": signal,
            "entry_close": float(r.close),
        })
    return store.save(TABLE, pd.DataFrame(rows))


def reconstruct(start: str, every: int = 5, top: int = 30,
                weights: dict | None = None) -> dict:
    """历史回放：从 start 起按 every 个交易日为步长复算当日推荐，批量入库。

    用 scorer.score_panel 一次性取全历史截面综合分，逐快照日取 Top-N 写库。回放行
    标注 signal='reconstruct'、action=''，以区别于实时快照（不含逐只逐日的择时动作，
    评估只用 score→前向收益，无需 action）。返回 {start,end,snapshots,rows}。
    """
    weights = weights or scorer.IC_WEIGHTS
    codes = research.universe()
    price, scores = scorer.score_panel(codes, weights)
    if scores.empty:
        return {"error": "无足够历史"}
    dates = [d for d in scores.index if d >= start]
    snap_dates = dates[::every]
    name_map = _name_map()
    rows = []
    for d in snap_dates:
        row = scores.loc[d].dropna()
        if row.empty:
            continue
        topn = row.sort_values(ascending=False).head(top)
        for rank, (code, sc) in enumerate(topn.items(), start=1):
            entry = price.at[d, code]
            if pd.isna(entry):
                continue
            rows.append({
                "as_of": d, "code": code, "name": name_map.get(code, ""),
                "rank": rank, "score": float(sc), "action": "",
                "signal": "reconstruct", "entry_close": float(entry),
            })
    if not rows:
        return {"error": "无快照"}
    n = store.save(TABLE, pd.DataFrame(rows))
    return {"start": snap_dates[0], "end": snap_dates[-1],
            "snapshots": len(snap_dates), "rows": n}


def _name_map() -> dict:
    if not store.has_table("stock_basic"):
        return {}
    b = store.query("SELECT code,name FROM stock_basic")
    return dict(zip(b["code"], b["name"]))
