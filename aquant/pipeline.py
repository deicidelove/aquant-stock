"""操作化例程：定时自动「更新数据 → 选股 → 出决策/持仓报告」。

- run_daily(): 收盘后跑。增量更新全市场日线+指数+资金流+板块，生成当日决策清单。
- run_quarterly(): 季度换仓日跑。按 IC 综合分出 Top-N 等权持仓组合（季度持有）。

报告写到 reports/，带日期戳，便于留痕与回看。供 cron/launchd 定时调度。
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from . import config, research
from .data import bulk, ingest, store
from .select import scorer

REPORTS = config.ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def _stamp() -> str:
    return pd.Timestamp.today().strftime("%Y-%m-%d")


def _safe(label: str, fn):
    """跑一个步骤，失败只记录不中断（数据源限流时降级）。"""
    try:
        r = fn()
        print(f"  ✓ {label}: {r}", flush=True)
        return r
    except Exception as e:
        print(f"  ! {label} 跳过: {str(e)[:80]}", flush=True)
        return None


def run_daily(update: bool = True, top: int = 30, signal: str = "ma_cross",
              drop_boards=None) -> dict:
    """每日例程。返回生成的报告路径。drop_boards 可选剔除板块（如 {"科创","创业"}）。"""
    t0 = time.time()
    day = _stamp()
    print(f"=== 每日例程 {day} ===", flush=True)

    if update:
        print("[更新] 全市场增量 + 指数 + 资金流 + 板块 ...", flush=True)
        _safe("股票列表", ingest.ingest_basic)
        _safe("沪深300", lambda: ingest.ingest_index("sh000300"))
        _safe("中证500", lambda: ingest.ingest_index("sh000905"))
        _safe("估值快照", ingest.ingest_valuation)   # 东财限流时自动跳过
        _safe("全市场日线", lambda: bulk.update_all(log_every=500)["ok"])
        _safe("资金流", ingest.ingest_fund_flow)   # 东财限流时自动跳过
        _safe("板块", ingest.ingest_sectors)

    print("[选股] 生成当日决策清单 ...", flush=True)
    # IC 策略选超跌反转股，不要求趋势向上（否则与因子方向冲突）
    picks = research.daily_picks(top=top, signal=signal, require_uptrend=False,
                                 drop_boards=drop_boards)
    md = research.to_markdown(picks, signal=signal)
    md_path = REPORTS / f"decision_{day}.md"
    md_path.write_text(md)
    print(f"  决策清单 → {md_path}", flush=True)

    # 推荐留痕：当日推荐结构化入库，供事后算前向收益/记分卡（持续优化的地基）
    from . import track
    _safe("推荐入库", lambda: f"{track.snapshot(top=top, signal=signal, drop_boards=drop_boards)} 行")

    print(f"=== 完成，用时 {(time.time()-t0)/60:.1f}m ===", flush=True)
    return {"date": day, "decision": str(md_path), "picks": len(picks)}


def run_quarterly(top: int = 50) -> dict:
    """季度换仓例程：按 IC 综合分出等权持仓组合（季度持有）。"""
    day = _stamp()
    codes = research.universe()
    ranked = scorer.score(codes, weights=scorer.IC_WEIGHTS, top=top)
    if ranked.empty:
        print("仓库数据不足。", flush=True)
        return {}
    ranked["weight"] = round(1.0 / len(ranked), 4)
    cols = [c for c in ["code", "name", "score", "weight"] if c in ranked.columns]
    out = ranked[cols]
    csv_path = REPORTS / f"portfolio_{day}.csv"
    out.to_csv(csv_path, index=False)
    print(f"季度持仓组合（Top{top}，等权）→ {csv_path}", flush=True)
    print(out.head(15).to_string(index=False), flush=True)
    return {"date": day, "portfolio": str(csv_path), "holdings": len(out)}
