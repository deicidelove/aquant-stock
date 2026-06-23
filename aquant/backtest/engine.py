"""轻量向量化回测引擎 + 绩效指标。

定位：研究用，不模拟撮合/盘口，按收盘价成交、可设手续费。
两种用法：
  1) backtest_signal(df, signal): 单只股票，signal 为持仓权重序列(0/1 或 0~1)。
  2) backtest_topn(...): 多因子选股的组合回测（周期换仓，等权 Top-N）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def perf_metrics(equity: pd.Series, returns: pd.Series | None = None) -> dict:
    """由净值序列计算绩效指标。"""
    equity = equity.dropna()
    if len(equity) < 2:
        return {}
    if returns is None:
        returns = equity.pct_change().dropna()
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1
    n = len(equity)
    ann_ret = (1 + total_ret) ** (TRADING_DAYS / n) - 1
    ann_vol = returns.std(ddof=0) * np.sqrt(TRADING_DAYS)
    sharpe = ann_ret / ann_vol if ann_vol else np.nan
    dd = equity / equity.cummax() - 1
    max_dd = dd.min()
    win_rate = (returns > 0).mean()
    calmar = ann_ret / abs(max_dd) if max_dd else np.nan
    return {
        "total_return": round(total_ret, 4),
        "annual_return": round(ann_ret, 4),
        "annual_vol": round(ann_vol, 4),
        "sharpe": round(sharpe, 3),
        "max_drawdown": round(max_dd, 4),
        "calmar": round(calmar, 3),
        "win_rate": round(win_rate, 4),
        "days": n,
    }


def backtest_signal(df: pd.DataFrame, signal: pd.Series,
                    fee: float = 0.0013, lag: int = 1) -> dict:
    """单只股票按信号回测。

    df: 含 date, close，按日期升序。
    signal: 与 df 对齐的目标仓位(0/1 或 0~1)。lag=1 表示信号当日生成、次日开盘按
            收盘价建仓（避免未来函数）。fee 为双边总费率（买卖各半）。
    返回 {metrics, equity}。
    """
    px = df["close"].reset_index(drop=True)
    pos = signal.reset_index(drop=True).shift(lag).fillna(0).clip(0, 1)
    ret = px.pct_change().fillna(0)
    turnover = pos.diff().abs().fillna(pos)
    strat_ret = pos * ret - turnover * (fee / 2)
    equity = (1 + strat_ret).cumprod()
    equity.index = pd.to_datetime(df["date"].values)
    m = perf_metrics(equity, strat_ret)
    # 基准：买入持有
    bench = (1 + ret).cumprod()
    m["benchmark_return"] = round(bench.iloc[-1] - 1, 4)
    return {"metrics": m, "equity": equity}


def _alloc_weights(held: list[str], rets: pd.DataFrame, i: int,
                   weighting: str, vol_window: int) -> pd.Series:
    """换仓日给持仓组合配权。equal=等权；inv_vol=反波动率（朴素风险平价）。"""
    if weighting == "inv_vol" and i > 0:
        window = rets.iloc[max(0, i - vol_window):i][held]
        vol = window.std(ddof=0).replace(0, np.nan)
        inv = (1.0 / vol).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        if inv.sum() > 0:
            return inv / inv.sum()
    return pd.Series(1.0 / len(held), index=held)


def backtest_topn(price_panel: pd.DataFrame, score_panel: pd.DataFrame,
                  top: int = 5, rebalance: int = 5, fee: float = 0.0013,
                  regime: pd.Series | None = None,
                  weighting: str = "equal", vol_window: int = 20) -> dict:
    """多因子选股组合回测（Top-N，定期换仓）。

    price_panel: index=date, columns=code 的收盘价宽表。
    score_panel: index=date, columns=code 的综合分宽表（同 price 对齐；可含 NaN）。
    rebalance: 每隔几个交易日按当日分数重选 Top-N（次日生效，避免未来函数）。
    weighting: 组合内加权方式。
        "equal"   —— 等权（默认，原行为）。
        "inv_vol" —— 反波动率加权（朴素风险平价）：按各持仓近 vol_window 日已实现波动率
                     的倒数归一化配权。低波个股拿更高权重，直接放大 aquant 验证过的
                     低波动异象暴露；用过去窗口算，无未来函数。
    vol_window: inv_vol 模式下计算波动率的回看窗口（交易日）。
    regime: 可选的大盘择时开关（index=date，1=持仓/0=空仓）。risk-off 时全部转现金，
            退出/再入会计入换手成本。同样 shift 一日生效，无未来函数。
    """
    price_panel = price_panel.sort_index()
    rets = price_panel.pct_change(fill_method=None).fillna(0)
    dates = price_panel.index
    weights = pd.DataFrame(0.0, index=dates, columns=price_panel.columns)

    held: list[str] = []
    w_vec: pd.Series | None = None
    for i, d in enumerate(dates):
        if i % rebalance == 0:
            row = score_panel.loc[d].dropna() if d in score_panel.index else pd.Series(dtype=float)
            if not row.empty:
                held = row.sort_values(ascending=False).head(top).index.tolist()
                w_vec = _alloc_weights(held, rets, i, weighting, vol_window)
        if held and w_vec is not None:
            weights.loc[d, held] = w_vec.reindex(held).fillna(0).to_numpy()

    # 次日生效
    eff = weights.shift(1).fillna(0)
    if regime is not None:
        reg = regime.reindex(dates).shift(1).fillna(0).clip(0, 1)
        eff = eff.mul(reg, axis=0)  # risk-off 日整体转现金
    turnover = eff.diff().abs().sum(axis=1).fillna(0)
    port_ret = (eff * rets).sum(axis=1) - turnover * (fee / 2)
    equity = (1 + port_ret).cumprod()
    m = perf_metrics(equity, port_ret)
    m["benchmark_return"] = round((1 + rets.mean(axis=1)).cumprod().iloc[-1] - 1, 4)  # 等权全池基准
    if regime is not None:
        m["time_in_market"] = round(float(regime.reindex(dates).shift(1).fillna(0).mean()), 3)
    return {"metrics": m, "equity": equity, "weights": eff}
