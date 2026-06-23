"""全市场：季度 IC 策略 + 大盘 regime 择时过滤 对比。

比较无 regime / 沪深300 MA120 / MA200 三种，看 regime 能否压低回撤、提升夏普。
复用 validate_fullmarket 的全量加载与综合分构建。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aquant import config                               # noqa: E402
from aquant.backtest import engine                      # noqa: E402
from aquant.select import scorer                         # noqa: E402
from aquant.signal import regime as regime_mod           # noqa: E402
from scripts.validate_fullmarket import load_all, price_matrix, composite  # noqa: E402

REB, TOP = 60, 50


def main():
    t0 = time.time()
    print("[1] 加载全市场 + 构建 IC 综合分 ...", flush=True)
    groups = load_all(min_history=250)
    price = price_matrix(groups)
    sp = composite(groups, scorer.IC_WEIGHTS, price.index)

    print("[2] 读沪深300 regime ...", flush=True)
    idx_close = regime_mod.index_close("sh000300")

    variants = {"无regime": None,
                "沪深300>MA120": regime_mod.trend_regime(idx_close, 120),
                "沪深300>MA200": regime_mod.trend_regime(idx_close, 200)}

    print(f"[3] 回测对比（季度换仓 reb={REB}，Top{TOP}，含费）：", flush=True)
    rows = []
    for name, reg in variants.items():
        reg_aligned = reg.reindex(price.index) if reg is not None else None
        bt = engine.backtest_topn(price, sp, top=TOP, rebalance=REB, regime=reg_aligned)
        m = bt["metrics"]
        rows.append({"方案": name, "总收益": m["total_return"], "年化": m["annual_return"],
                     "夏普": m["sharpe"], "最大回撤": m["max_drawdown"], "胜率": m["win_rate"],
                     "在场比例": m.get("time_in_market", 1.0)})
    res = pd.DataFrame(rows)
    print(res.to_string(index=False), flush=True)
    res.to_csv(config.DATA_DIR / "regime_compare.csv", index=False)
    print(f"\n总用时 {(time.time()-t0)/60:.1f}m\nDONE", flush=True)


if __name__ == "__main__":
    main()
