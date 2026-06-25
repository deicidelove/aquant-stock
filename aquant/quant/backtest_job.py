"""回测任务：解析权重 → score_panel → backtest_topn → 净值+绩效（含基准曲线）。"""
from __future__ import annotations

import pandas as pd

from ..backtest.engine import backtest_topn
from ..data import store
from ..select import scorer
from .. import research
from . import jobs


def resolve_weights(weights) -> dict:
    if weights == "ic":
        return scorer.IC_WEIGHTS
    if weights == "momentum":
        return scorer.MOMENTUM_WEIGHTS
    if isinstance(weights, dict) and weights:
        return weights
    return scorer.IC_WEIGHTS


def _benchmark_series(dates: pd.Index) -> dict[str, float]:
    """沪深300 归一化到 1.0 的基准曲线（对齐回测日期）；无数据返回空。"""
    if not store.has_table("index_daily"):
        return {}
    idx = store.query("SELECT date, close FROM index_daily WHERE code = 'sh000300' ORDER BY date")
    if idx.empty:
        return {}
    s = idx.set_index("date")["close"].reindex([str(d) for d in dates]).ffill()
    base = s.dropna()
    if base.empty:
        return {}
    return (s / base.iloc[0]).to_dict()


def run_backtest(params: dict) -> dict:
    weights = resolve_weights(params.get("weights", "ic"))
    top_n = int(params.get("top_n", 5))
    rebalance = int(params.get("rebalance_every", 5))
    min_history = int(params.get("min_history", 250))
    codes = research.universe(drop_boards=set(params["drop_boards"]) if params.get("drop_boards") else None)
    price, score = scorer.score_panel(codes, weights, min_history=min_history)
    if price.empty or score.empty:
        return {"nav": [], "metrics": {}, "top_n": top_n, "rebalance_every": rebalance}
    res = backtest_topn(price, score, top=top_n, rebalance=rebalance)
    equity = res["equity"].dropna()
    bench = _benchmark_series(equity.index)
    nav = [{"date": str(d), "equity": round(float(v), 4),
            "benchmark": round(float(bench[str(d)]), 4) if str(d) in bench else None}
           for d, v in equity.items()]
    return {"nav": nav, "metrics": res["metrics"], "top_n": top_n, "rebalance_every": rebalance}


jobs.register("backtest", run_backtest)
