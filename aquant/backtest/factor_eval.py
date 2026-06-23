"""因子有效性检验（IC 分析）+ 滚动截面综合分面板。

IC（信息系数）= 每个截面上「因子值」与「未来收益」的横截面相关系数。
- IC 均值显著 ≠ 0 → 因子有预测力；正=越大越涨。
- IR = IC均值 / IC标准差，衡量稳定性。
这是判断「因子到底有没有用」的标准量化手段，避免只靠一次回测的运气。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data import store
from ..factors import registry, technical  # noqa: F401 触发注册


def _wide(codes: list[str], col: str) -> pd.DataFrame:
    """把多只股票的某列拼成 index=date, columns=code 的宽表。"""
    data = {}
    for c in codes:
        d = store.load_daily(c)
        if not d.empty:
            data[c] = d.set_index("date")[col]
    return pd.DataFrame(data).sort_index()


def factor_wide(codes: list[str], factor: str) -> pd.DataFrame:
    """单因子的 index=date, columns=code 宽表。"""
    fn = registry.get(factor).fn
    data = {}
    for c in codes:
        d = store.load_daily(c)
        if len(d) >= 60:
            data[c] = pd.Series(fn(d).values, index=d["date"].values)
    return pd.DataFrame(data).sort_index()


def ic_series(codes: list[str], factor: str, fwd: int = 5) -> pd.Series:
    """逐截面计算因子值与未来 fwd 日收益的 Spearman 相关（rank IC）。"""
    close = _wide(codes, "close")
    fwd_ret = close.shift(-fwd) / close - 1
    fac = factor_wide(codes, factor).reindex_like(close)
    direction = registry.get(factor).direction
    ics = []
    for d in close.index:
        f = fac.loc[d] if d in fac.index else None
        r = fwd_ret.loc[d]
        if f is None:
            continue
        pair = pd.concat([f, r], axis=1).dropna()
        if len(pair) >= 5:
            ic = pair.iloc[:, 0].rank().corr(pair.iloc[:, 1].rank())
            ics.append((d, ic * direction))
    return pd.Series(dict(ics)).dropna()


def evaluate(codes: list[str], factors: list[str] | None = None,
             fwd: int = 5) -> pd.DataFrame:
    """对一组因子算 IC 统计，返回按 |IR| 排序的表。"""
    factors = factors or list(registry.all_factors())
    rows = []
    for f in factors:
        ic = ic_series(codes, f, fwd=fwd)
        if ic.empty:
            continue
        mean, std = ic.mean(), ic.std(ddof=0)
        rows.append({
            "factor": f,
            "ic_mean": round(mean, 4),
            "ic_std": round(std, 4),
            "ir": round(mean / std, 3) if std else np.nan,
            "ic_win": round((ic > 0).mean(), 3),  # IC 为正的比例
            "n": len(ic),
        })
    out = pd.DataFrame(rows)
    return out.reindex(out["ir"].abs().sort_values(ascending=False).index) if not out.empty else out


def composite_score_panel(codes: list[str], weights: dict[str, float]) -> pd.DataFrame:
    """滚动截面综合分宽表（index=date, columns=code）：每个截面对各因子做
    横截面 Z-score、按方向与权重合成。供 backtest_topn 做严谨的组合回测。
    """
    close = _wide(codes, "close")
    total = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    for f, w in weights.items():
        fac = factor_wide(codes, f).reindex_like(close)
        direction = registry.get(f).direction
        mu = fac.mean(axis=1)
        sd = fac.std(axis=1, ddof=0).replace(0, np.nan)
        z = fac.sub(mu, axis=0).div(sd, axis=0) * direction
        total = total.add(z.fillna(0) * w, fill_value=0)
    return total
