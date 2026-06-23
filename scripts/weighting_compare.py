"""组合内加权方式对比：等权 vs 反波动率（朴素风险平价）。

复用清洁域全市场 + IC 综合分面板，按季度换仓（默认 reb=63）对比两种配权的
年化/夏普/回撤/Calmar。验证「风险平价是否真比等权提升风险调整后收益」——
契合 aquant 先回测再定稿的纪律，不验证不进核心。

用法：python scripts/weighting_compare.py [--top 50] [--rebalance 63]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aquant import config                       # noqa: E402
from aquant.backtest import engine              # noqa: E402
from aquant.data import store                   # noqa: E402
from aquant.factors import registry             # noqa: E402
from aquant.select import scorer                # noqa: E402
from scripts.validate_fullmarket import composite, load_all, price_matrix  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-history", type=int, default=250)
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--rebalance", type=int, default=63)  # ~季度
    ap.add_argument("--vol-window", type=int, default=20)
    args = ap.parse_args()

    t0 = time.time()
    print("[1] 加载清洁域全市场 ...", flush=True)
    groups = load_all(args.min_history)
    from aquant.research import universe
    clean = set(universe(min_history=args.min_history))
    groups = {c: g for c, g in groups.items() if c in clean}
    price = price_matrix(groups)
    print(f"    清洁域 {len(groups)} 只，价格面板 {price.shape}", flush=True)

    print("[2] 构建 IC 加权综合分面板 ...", flush=True)
    sp = composite(groups, scorer.IC_WEIGHTS, price.index)

    print(f"[3] 季度换仓(reb={args.rebalance}) Top{args.top}，含费0.13%：", flush=True)
    rows = []
    for tag, kw in [("等权", {}), ("风险平价(inv_vol)", {"weighting": "inv_vol",
                                                         "vol_window": args.vol_window})]:
        bt = engine.backtest_topn(price, sp, top=args.top, rebalance=args.rebalance, **kw)
        m = bt["metrics"]
        rows.append({"配权": tag, "总收益": m["total_return"], "年化": m["annual_return"],
                     "年化波动": m["annual_vol"], "夏普": m["sharpe"],
                     "最大回撤": m["max_drawdown"], "Calmar": m["calmar"],
                     "胜率": m["win_rate"]})
    res = pd.DataFrame(rows)
    print(res.to_string(index=False), flush=True)
    out = config.DATA_DIR / "weighting_compare.csv"
    res.to_csv(out, index=False)
    print(f"\n  → {out}\n总用时 {(time.time()-t0)/60:.1f}m\nDONE", flush=True)


if __name__ == "__main__":
    main()
