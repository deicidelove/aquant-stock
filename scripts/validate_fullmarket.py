"""全市场策略复验（优化版：一次性加载 + 内存截面计算）。

避免逐只开数据库连接（5207×9≈4.7万次）：单查询取全量 → 按 code 分组 →
逐因子构建 date×code 矩阵、做横截面 z-score、按方向与权重累加成综合分 →
向量化组合回测。比较 IC加权 在不同换仓周期下 vs 等权基准。

用法：python scripts/validate_fullmarket.py [--min-history 250] [--top 50]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aquant import config              # noqa: E402
from aquant.data import store          # noqa: E402
from aquant.factors import registry, technical  # noqa: E402,F401
from aquant.backtest import engine     # noqa: E402
from aquant.select import scorer        # noqa: E402


def load_all(min_history: int) -> dict[str, pd.DataFrame]:
    """单查询取全量日线，按 code 分组成 {code: df(按date升序)}。"""
    t = time.time()
    df = store.query(
        "SELECT code, date, open, high, low, close, volume, amount, turnover "
        "FROM daily_bar ORDER BY code, date")
    print(f"  全量加载 {len(df):,} 行，用时 {time.time()-t:.1f}s", flush=True)
    groups = {c: g.reset_index(drop=True) for c, g in df.groupby("code", sort=False)
              if len(g) >= min_history}
    print(f"  历史>={min_history} 的股票 {len(groups)} 只", flush=True)
    return groups


def price_matrix(groups: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame({c: g.set_index("date")["close"] for c, g in groups.items()}).sort_index()


def composite(groups: dict[str, pd.DataFrame], weights: dict[str, float],
              index: pd.Index) -> pd.DataFrame:
    """逐因子构建矩阵→截面z-score→按方向×权重累加，得 date×code 综合分。"""
    total = pd.DataFrame(0.0, index=index, columns=list(groups))
    for f, w in weights.items():
        fn = registry.get(f).fn
        direction = registry.get(f).direction
        mat = pd.DataFrame(
            {c: pd.Series(fn(g).values, index=g["date"].values) for c, g in groups.items()}
        ).reindex(index)
        mu = mat.mean(axis=1)
        sd = mat.std(axis=1, ddof=0).replace(0, np.nan)
        z = mat.sub(mu, axis=0).div(sd, axis=0) * direction
        total = total.add(z.fillna(0) * w, fill_value=0)
        del mat, z
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-history", type=int, default=250)
    ap.add_argument("--top", type=int, default=50)
    args = ap.parse_args()

    t0 = time.time()
    print("[1] 加载全市场（清洁域：剔除 ST/次新/低流动性）...", flush=True)
    groups = load_all(args.min_history)
    from aquant.research import universe
    clean = set(universe(min_history=args.min_history))
    before = len(groups)
    groups = {c: g for c, g in groups.items() if c in clean}
    print(f"    清洁域过滤：{before} → {len(groups)} 只", flush=True)
    price = price_matrix(groups)
    print(f"    价格面板 {price.shape}", flush=True)

    print("[2] 构建 IC 加权综合分面板 ...", flush=True)
    sp = composite(groups, scorer.IC_WEIGHTS, price.index)

    print(f"[3] 回测（Top{args.top}，含费0.13%，基准=全市场等权买入持有）：", flush=True)
    bench = (1 + price.pct_change(fill_method=None).fillna(0).mean(axis=1)).cumprod().iloc[-1] - 1
    rows = []
    for reb in (5, 20, 60):
        bt = engine.backtest_topn(price, sp, top=args.top, rebalance=reb)
        m = bt["metrics"]
        rows.append({"换仓日": reb, "总收益": m["total_return"], "年化": m["annual_return"],
                     "夏普": m["sharpe"], "最大回撤": m["max_drawdown"], "胜率": m["win_rate"]})
    res = pd.DataFrame(rows)
    print(res.to_string(index=False), flush=True)
    print(f"\n  全市场等权基准总收益: {bench:.4f}", flush=True)
    res.to_csv(config.DATA_DIR / "fullmarket_validate.csv", index=False)
    print(f"\n总用时 {(time.time()-t0)/60:.1f}m\nDONE", flush=True)


if __name__ == "__main__":
    main()
