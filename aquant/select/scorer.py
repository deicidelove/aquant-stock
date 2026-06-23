"""多因子横截面打分选股。

思路：在某个交易日，对股票池里每只股票计算各因子的最新值，做横截面 Z-score
标准化（按因子方向调正），加权求和得综合分，排序取 Top-N 候选池。

这是“选什么股”的核心：把多个维度的强弱压成一个可比的分数。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data import store
from ..factors import registry
from ..factors import technical  # noqa: F401 触发因子注册

# 动量风格权重（朴素先验：越强越买）。注意：IC 检验显示其在 5 日尺度预测力为负。
MOMENTUM_WEIGHTS: dict[str, float] = {
    "mom_20": 1.0,
    "mom_60": 1.0,
    "trend_align": 1.5,
    "rsi_14": 0.5,
    "vol_ratio_5_20": 0.5,
    "macd_hist": 1.0,
    "volatility_20": 0.8,
    "ma_bias_20": 0.5,
}

# IC 加权（数据驱动）：权重=各因子实测 IR（带符号），自动把负向因子翻转。
# 由 backtest.factor_eval.evaluate 在 600 只样本、未来5日上测得（见 data_store/factor_ic.csv）。
# 实质是 A 股「低波动 + 短期反转 + 不追高」组合。
IC_WEIGHTS: dict[str, float] = {
    "volatility_20": 0.47,
    "ma_bias_20": 0.37,
    "vol_ratio_5_20": -0.42,
    "mom_20": -0.41,
    "turnover_mean_20": -0.41,
    "trend_align": -0.37,
    "mom_60": -0.33,
    "rsi_14": -0.31,
    "macd_hist": -0.25,
}

# 默认采用数据驱动的 IC 权重
DEFAULT_WEIGHTS = IC_WEIGHTS


def _zscore(s: pd.Series) -> pd.Series:
    mu, sd = s.mean(), s.std(ddof=0)
    if not sd or np.isnan(sd):
        return pd.Series(0.0, index=s.index)
    return (s - mu) / sd


def factor_panel(codes: list[str], weights: dict[str, float] | None = None,
                 as_of: str | None = None) -> pd.DataFrame:
    """构建截面因子表：每只股票取 as_of（含）之前最新一日的各因子值。

    返回 DataFrame，index=code，列=各因子 + name。
    """
    weights = weights or DEFAULT_WEIGHTS
    names = list(weights)
    rows = {}
    for code in codes:
        df = store.load_daily(code)
        if df.empty:
            continue
        if as_of:
            df = df[df["date"] <= as_of]
        if len(df) < 60:  # 因子需要足够历史
            continue
        fac = registry.compute(df, names).iloc[-1]
        rows[code] = {n: fac[n] for n in names}
    panel = pd.DataFrame.from_dict(rows, orient="index")
    return panel


def score_fast(codes: list[str] | None = None, weights: dict[str, float] | None = None,
               top: int = 50, min_history: int = 60) -> pd.DataFrame:
    """快速横截面打分：一次性 SQL 取全量 → 按 code 分组内存计算最新截面分。

    避免逐只开数据库连接（score() 对全市场会很慢）。给定 codes 则只算这些。
    返回按综合分降序的 DataFrame（code,name,score）。
    """
    weights = weights or DEFAULT_WEIGHTS
    names = list(weights)
    df = store.query("SELECT code,date,open,high,low,close,volume,amount,turnover "
                     "FROM daily_bar ORDER BY code,date")
    keep = set(codes) if codes is not None else None
    latest: dict[str, dict] = {}
    for code, g in df.groupby("code", sort=False):
        if keep is not None and code not in keep:
            continue
        if len(g) < min_history:
            continue
        g = g.reset_index(drop=True)
        latest[code] = {n: registry.get(n).fn(g).iloc[-1] for n in names}
    panel = pd.DataFrame.from_dict(latest, orient="index")
    if panel.empty:
        return pd.DataFrame()

    total = pd.Series(0.0, index=panel.index)
    for n, w in weights.items():
        if n in panel.columns:
            total = total.add(_zscore(panel[n]) * registry.get(n).direction * w, fill_value=0)
    out = pd.DataFrame({"score": total})
    basic = store.query("SELECT code,name FROM stock_basic") if store.has_table("stock_basic") else pd.DataFrame()
    if not basic.empty:
        out = out.join(basic.set_index("code")["name"])
    out.index.name = "code"
    return out.sort_values("score", ascending=False).head(top).reset_index()


def score_panel(codes: list[str], weights: dict[str, float] | None = None,
                min_history: int = 250):
    """全历史截面打分面板：单查询取全量 → 价格宽表 + 综合分宽表。

    返回 (price, total)：均为 index=date、columns=code 的宽表。total[d] 即第 d 日
    全市场 IC 综合分截面（已按因子方向 z-score 加权）。供需要逐历史日截面的场景
    复用（季度回放、推荐回放），避免逐只逐日重算。
    """
    weights = weights or DEFAULT_WEIGHTS
    df = store.query("SELECT code,date,open,high,low,close,volume,amount,turnover "
                     "FROM daily_bar ORDER BY code,date")
    keep = set(codes)
    groups = {c: g.reset_index(drop=True) for c, g in df.groupby("code", sort=False)
              if c in keep and len(g) >= min_history}
    price = pd.DataFrame({c: g.set_index("date")["close"] for c, g in groups.items()}).sort_index()
    total = pd.DataFrame(0.0, index=price.index, columns=list(groups))
    for n, w in weights.items():
        fn, direction = registry.get(n).fn, registry.get(n).direction
        mat = pd.DataFrame({c: pd.Series(fn(g).values, index=g["date"].values)
                            for c, g in groups.items()}).reindex(price.index)
        mu, sd = mat.mean(axis=1), mat.std(axis=1, ddof=0).replace(0, np.nan)
        total = total.add((mat.sub(mu, axis=0).div(sd, axis=0) * direction).fillna(0) * w, fill_value=0)
    return price, total


def score(codes: list[str], weights: dict[str, float] | None = None,
          as_of: str | None = None, top: int = 20) -> pd.DataFrame:
    """对股票池打分，返回按综合分降序的 DataFrame（含各因子贡献）。"""
    weights = weights or DEFAULT_WEIGHTS
    panel = factor_panel(codes, weights, as_of)
    if panel.empty:
        return pd.DataFrame()

    contrib = pd.DataFrame(index=panel.index)
    total = pd.Series(0.0, index=panel.index)
    for n, w in weights.items():
        if n not in panel.columns:
            continue
        direction = registry.get(n).direction
        z = _zscore(panel[n]) * direction
        contrib[n] = z * w
        total = total.add(z * w, fill_value=0)

    out = pd.DataFrame({"score": total})
    out = out.join(contrib.add_prefix("c_"))
    # 附名称
    basic = store.query("SELECT code, name FROM stock_basic") if store.has_table("stock_basic") else pd.DataFrame()
    if not basic.empty:
        out = out.join(basic.set_index("code")["name"])
    out = out.sort_values("score", ascending=False)
    out.index.name = "code"
    return out.head(top).reset_index()
