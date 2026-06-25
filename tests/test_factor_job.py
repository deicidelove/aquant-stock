def test_run_factor_ic_smoke(seed_db):
    from aquant.quant import factor_job
    out = factor_job.run_factor_ic({"factors": ["mom_20", "volatility_20"], "fwd": 5})
    assert "rows" in out and out["fwd"] == 5
    assert isinstance(out["rows"], list)


def test_factor_ic_registered():
    import aquant.quant.factor_job  # noqa: F401
    from aquant.quant import jobs
    assert "factor_ic" in jobs._RUNNERS
