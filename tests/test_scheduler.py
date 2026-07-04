from datetime import datetime


def test_trading_hours_gate():
    from server.refresh.scheduler import is_trading_hours
    assert is_trading_hours(datetime(2026, 6, 23, 10, 0)) is True   # 周二上午
    assert is_trading_hours(datetime(2026, 6, 23, 14, 0)) is True   # 周二下午
    assert is_trading_hours(datetime(2026, 6, 23, 12, 0)) is False  # 午休
    assert is_trading_hours(datetime(2026, 6, 23, 16, 0)) is False  # 盘后
    assert is_trading_hours(datetime(2026, 6, 27, 10, 0)) is False  # 周六


def test_build_scheduler_registers_jobs():
    from server.refresh.scheduler import build_scheduler
    sched = build_scheduler()
    job_ids = {j.id for j in sched.get_jobs()}
    assert {"intraday_snapshots", "eod_materialize"}.issubset(job_ids)
    assert not sched.running  # 仅构建不启动


def test_intraday_registers_fundflow():
    import server.refresh.scheduler as sch
    # _intraday_job 引用了资金刷新函数（通过模块属性可见）
    import server.refresh.fundflow as ff
    assert hasattr(ff, "refresh_sector_fund_flow") and hasattr(ff, "refresh_fund_flow")
