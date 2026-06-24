"""物化全市场因子综合分：收盘后批量计算落 factor_score，API 查表替代每次现算。"""
from __future__ import annotations

from aquant.data import store
from aquant.select import scorer
from aquant import research


def materialize_scores(top: int = 10000) -> int:
    """计算全市场综合分写 factor_score（as_of=daily_bar 最新日），返回写入行数。"""
    as_of = store.max_date("daily_bar")
    if as_of is None:
        return 0
    ranked = scorer.score_fast(codes=research.universe(), top=top)
    if ranked.empty:
        return 0
    ranked = ranked.copy()
    ranked["as_of"] = as_of
    cols = [c for c in ("code", "name", "score", "as_of") if c in ranked.columns]
    return store.save("factor_score", ranked[cols])


def read_top_scores(top: int = 50):
    """读最新 as_of 的前 top 名（按 score 降序）。"""
    if not store.has_table("factor_score"):
        import pandas as pd
        return pd.DataFrame()
    return store.query(
        "SELECT code, name, score, as_of FROM factor_score "
        "WHERE as_of = (SELECT max(as_of) FROM factor_score) "
        "ORDER BY score DESC LIMIT ?", [top])
