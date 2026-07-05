"""后台刷新调度：盘中每 2min 拉快照（交易时段门控），收盘后物化评分。"""
from __future__ import annotations

from datetime import datetime, time

from apscheduler.schedulers.background import BackgroundScheduler

from server.refresh import snapshots, scores, fundflow

_AM = (time(9, 30), time(11, 30))
_PM = (time(13, 0), time(15, 0))


def is_trading_hours(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    t = now.time()
    return (_AM[0] <= t <= _AM[1]) or (_PM[0] <= t <= _PM[1])


def _intraday_job() -> None:
    if not is_trading_hours(datetime.now()):
        return
    for fn in (snapshots.refresh_quotes, snapshots.refresh_sectors,
               fundflow.refresh_sector_fund_flow, fundflow.refresh_fund_flow):
        try:
            fn()
        except Exception:  # noqa: BLE001 后台任务失败不影响其他
            pass


def _eod_job() -> None:
    try:
        scores.materialize_scores()
    except Exception:  # noqa: BLE001
        pass
    try:
        from server.refresh.research_cache import prefetch_research
        prefetch_research()
    except Exception:  # noqa: BLE001
        pass
    try:
        from server.refresh.lhb import refresh_lhb
        refresh_lhb()
    except Exception:  # noqa: BLE001
        pass


def build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="Asia/Shanghai")
    sched.add_job(_intraday_job, "interval", minutes=2, id="intraday_snapshots")
    sched.add_job(_eod_job, "cron", hour=15, minute=30, id="eod_materialize")
    return sched
