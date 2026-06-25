def test_submit_run_get_lifecycle(seed_db):
    from aquant.quant import jobs
    jobs.register("echo", lambda params: {"echoed": params["x"] * 2})
    jid = jobs.submit_job("echo", {"x": 21})
    # AQUANT_JOBS_SYNC=1 → submit 内已同步跑完
    job = jobs.get_job(jid)
    assert job["status"] == "done"
    assert job["kind"] == "echo"
    assert job["result"] == {"echoed": 42}


def test_job_error_captured(seed_db):
    from aquant.quant import jobs
    def boom(params):
        raise ValueError("nope")
    jobs.register("boom", boom)
    jid = jobs.submit_job("boom", {})
    job = jobs.get_job(jid)
    assert job["status"] == "error"
    assert "nope" in job["error"]


def test_get_missing_job(seed_db):
    from aquant.quant import jobs
    assert jobs.get_job("nosuch") is None
