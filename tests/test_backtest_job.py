def test_resolve_weights():
    from aquant.quant import backtest_job
    from aquant.select import scorer
    assert backtest_job.resolve_weights("ic") == scorer.IC_WEIGHTS
    assert backtest_job.resolve_weights("momentum") == scorer.MOMENTUM_WEIGHTS
    assert backtest_job.resolve_weights({"mom_20": 1.0}) == {"mom_20": 1.0}


def test_run_backtest_smoke(seed_db):
    from aquant.quant import backtest_job
    out = backtest_job.run_backtest({"weights": "ic", "top_n": 2, "rebalance_every": 5, "min_history": 60})
    assert "metrics" in out and "nav" in out
    assert out["top_n"] == 2
    assert isinstance(out["nav"], list)
    if out["nav"]:
        assert set(out["nav"][0]) >= {"date", "equity"}


def test_backtest_registered():
    import aquant.quant.backtest_job  # noqa: F401 触发注册
    from aquant.quant import jobs
    assert "backtest" in jobs._RUNNERS
