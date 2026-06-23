"""模拟盘历史种子 + 绩效分析 + 反馈。

- seed(): 从过去某日按 IC 策略建仓、季度换仓、定期盯市到今天，populate 出真实净值
  曲线（用已有历史数据，诚实标注为回放）。让闭环立刻有东西可看、可分析。
- performance(): 净值曲线 → 年化/夏普/回撤 + 对标沪深300。
- attribution(): 当前持仓盈亏归因（赢家/输家）。
- feedback(): 持仓收益 vs 建仓时综合分的关系，反馈选股有效性。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import account
from ..data import store
from ..factors import registry, technical  # noqa: F401
from ..select import scorer
from .. import research

TRADING_DAYS = 252


def _bulk_panels(weights: dict, min_history: int = 250):
    """单查询取全量 → 价格宽表 + IC 综合分宽表（截面 z-score 加权）。

    清洁域股票池上的全历史截面打分，委托给 scorer.score_panel（与推荐回放共用）。
    """
    codes = research.universe(min_history=min_history)
    return scorer.score_panel(codes, weights, min_history=min_history)


def seed(start: str, top: int = 50, rebalance_every: int = 60,
         mark_every: int = 5, capital: float = account.INIT_CAPITAL) -> dict:
    """从 start 起按 IC 策略回放建仓到最新交易日，populate 模拟盘。"""
    account.reset(capital)
    price, scores = _bulk_panels(scorer.IC_WEIGHTS)
    dates = [d for d in price.index if d >= start]
    if not dates:
        return {"error": "无足够历史"}
    n_reb = 0
    for i, d in enumerate(dates):
        if i % rebalance_every == 0:
            row = scores.loc[d].dropna()
            target = row.sort_values(ascending=False).head(top).index.tolist()
            account.rebalance(d, target, note=f"reb#{n_reb}")
            n_reb += 1
        elif i % mark_every == 0:
            account.mark(d)
    account.mark(dates[-1])  # 收尾盯市
    return {"start": dates[0], "end": dates[-1], "rebalances": n_reb,
            "final_nav": account.total_value(dates[-1])}


def _benchmark(dates: pd.Index, code: str = "sh000300") -> pd.Series | None:
    if not store.has_table("index_daily"):
        return None
    df = store.query("SELECT date, close FROM index_daily WHERE code = ? ORDER BY date", [code])
    if df.empty:
        return None
    s = df.set_index("date")["close"]
    s = s[s.index.isin(dates)]
    return s / s.iloc[0] if len(s) else None


def performance() -> dict:
    nav = account.nav_series()
    if len(nav) < 2:
        return {}
    eq = nav.set_index("date")["total"]
    ret = eq.pct_change().dropna()
    total_ret = eq.iloc[-1] / eq.iloc[0] - 1
    # 年化按真实日历跨度（而非快照个数）
    span_days = (pd.to_datetime(eq.index[-1]) - pd.to_datetime(eq.index[0])).days
    years = max(span_days / 365.25, 1e-6)
    ann = (1 + total_ret) ** (1 / years) - 1
    # 夏普：快照频率年化（periods_per_year 由实际快照数/年限推得）
    periods_per_year = len(ret) / years if years > 0 else len(ret)
    vol = ret.std(ddof=0) * np.sqrt(periods_per_year)
    sharpe = ann / vol if vol else np.nan
    dd = (eq / eq.cummax() - 1).min()
    out = {"start": nav["date"].iloc[0], "end": nav["date"].iloc[-1],
           "total_return": round(total_ret, 4), "annual_return": round(ann, 4),
           "sharpe": round(sharpe, 3), "max_drawdown": round(dd, 4),
           "final_value": round(eq.iloc[-1], 0)}
    bench = _benchmark(eq.index)
    if bench is not None and len(bench) > 1:
        out["benchmark_hs300"] = round(bench.iloc[-1] / bench.iloc[0] - 1, 4)
        out["excess"] = round(total_ret - (bench.iloc[-1] / bench.iloc[0] - 1), 4)
    return out


def attribution(date: str | None = None) -> pd.DataFrame:
    """当前持仓盈亏归因：每只浮动盈亏与收益率。"""
    pos = account.positions()
    if pos.empty:
        return pd.DataFrame()
    date = date or account.nav_series()["date"].iloc[-1]
    px = account.closes_on(date, pos["code"].tolist())
    basic = store.query("SELECT code,name FROM stock_basic") if store.has_table("stock_basic") else pd.DataFrame()
    name_map = dict(zip(basic["code"], basic["name"])) if not basic.empty else {}
    rows = []
    for r in pos.itertuples(index=False):
        last = px.get(r.code, r.avg_cost)
        pnl = (last - r.avg_cost) * r.shares
        rows.append({"code": r.code, "name": name_map.get(r.code, ""),
                     "shares": r.shares, "avg_cost": r.avg_cost, "last": round(last, 3),
                     "ret": round(last / r.avg_cost - 1, 4) if r.avg_cost else 0,
                     "pnl": round(pnl, 0)})
    return pd.DataFrame(rows).sort_values("pnl", ascending=False)
