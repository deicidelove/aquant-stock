"""因子 IC 任务：对 universe 跑各因子 IC/IR 排名。"""
from __future__ import annotations

from ..backtest import factor_eval
from .. import research
from . import jobs


def run_factor_ic(params: dict) -> dict:
    fwd = int(params.get("fwd", 5))
    factors = params.get("factors")  # None → 全因子
    codes = research.universe()
    df = factor_eval.evaluate(codes, factors=factors, fwd=fwd)
    rows = df.to_dict(orient="records") if not df.empty else []
    return {"rows": rows, "fwd": fwd}


jobs.register("factor_ic", run_factor_ic)
