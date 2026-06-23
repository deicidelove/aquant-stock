"""全市场批量入库：拉全 A 股日线，增量、可续跑、带进度。

特点：
- 增量：已入库的股票只补最新缺口（store.max_date 断点），重复跑很快。
- 可续跑：中断后再跑会跳过已是最新的股票。
- 限流友好：每只之间轻微 sleep；东财熔断后自动全程走新浪。
- 进度/ETA：每 N 只打印一次；失败代码单独汇总，便于补拉。
"""
from __future__ import annotations

import time

import pandas as pd

from . import ingest, store
from .sources import akshare_source as src


def _today() -> str:
    return pd.Timestamp.today().strftime("%Y-%m-%d")


def backfill_lagging(throttle: float = 0.15, log_every: int = 50) -> dict:
    """把"落后"的股票补到全库最新交易日。

    用全库已有的最大日期作为目标（而非日历今天），只更新 max_date 落后的股票，
    跳过已是最新的——避免在无新数据的日子里全市场空扫。
    """
    if not store.has_table("daily_bar"):
        return {"ok": 0, "fail": 0, "lagging": 0}
    target = store.query("SELECT max(date) d FROM daily_bar")["d"].iloc[0]
    lagging = store.query(
        "SELECT code, max(date) mx FROM daily_bar GROUP BY code HAVING max(date) < ?",
        [target])["code"].tolist()
    print(f"全库最新日期 {target}，落后股票 {len(lagging)} 只，开始补齐 ...", flush=True)

    t0 = time.time()
    ok = fail = rows = 0
    failures: list[str] = []
    for i, code in enumerate(lagging, 1):
        try:
            rows += ingest.ingest_daily(code, incremental=True)
            ok += 1
        except Exception:
            fail += 1
            failures.append(code)
        if throttle:
            time.sleep(throttle)
        if i % log_every == 0:
            el = time.time() - t0
            print(f"  [{i}/{len(lagging)}] ok={ok} fail={fail} rows={rows} "
                  f"用时{el/60:.1f}m ETA{el/i*(len(lagging)-i)/60:.1f}m "
                  f"东财熔断={src._em['open']}", flush=True)
    print(f"补齐完成：ok={ok} fail={fail} rows={rows} 用时{(time.time()-t0)/60:.1f}m", flush=True)
    if failures:
        print(f"失败 {len(failures)} 只：{failures[:30]}", flush=True)
    return {"target": target, "lagging": len(lagging), "ok": ok, "fail": fail,
            "rows": rows, "failures": failures}


def update_all(start: str | None = None, throttle: float = 0.15,
               log_every: int = 50, skip_bj: bool = True,
               only_missing_today: bool = True) -> dict:
    """全市场增量入库。

    start: 首次入库的历史起点（缺省用 config.HISTORY_START）。
    skip_bj: 跳过北交所（8/4 开头，多数策略不覆盖）。
    only_missing_today: 已更新到最近交易日的股票直接跳过（增量续跑核心）。
    """
    t0 = time.time()
    basic = src.stock_list()
    store.save("stock_basic", basic)
    codes = basic["code"].tolist()
    if skip_bj:
        codes = [c for c in codes if not c.startswith(("8", "4"))]

    total = len(codes)
    done = ok = fail = skipped = 0
    rows_written = 0
    failures: list[str] = []
    today = _today()

    print(f"全市场入库启动：{total} 只（skip_bj={skip_bj}）")
    for code in codes:
        done += 1
        try:
            if only_missing_today:
                last = store.max_date("daily_bar", code)
                if last and last >= today:
                    skipped += 1
                    continue
            n = ingest.ingest_daily(code, start=start, incremental=True)
            rows_written += n
            ok += 1
        except Exception as e:  # 单只失败不阻断
            fail += 1
            failures.append(code)
        if throttle:
            time.sleep(throttle)
        if done % log_every == 0:
            el = time.time() - t0
            eta = el / done * (total - done)
            print(f"  [{done}/{total}] ok={ok} skip={skipped} fail={fail} "
                  f"rows={rows_written} | 用时{el/60:.1f}m ETA{eta/60:.1f}m "
                  f"| 东财熔断={src._em['open']}", flush=True)

    summary = {"total": total, "ok": ok, "skipped": skipped, "fail": fail,
               "rows_written": rows_written, "minutes": round((time.time() - t0) / 60, 1),
               "failures": failures}
    print(f"\n完成：ok={ok} skip={skipped} fail={fail} rows={rows_written} "
          f"用时{summary['minutes']}m")
    if failures:
        print(f"失败 {len(failures)} 只（可重跑补拉）：{failures[:30]}{' ...' if len(failures) > 30 else ''}")
    return summary
