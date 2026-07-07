from aquant.data import research_cache as rc


def test_save_and_read_report():
    assert rc.read_report("600000") is None  # 无表/无数据
    rep = {"code": "600000", "verdict": {"stance": "买入/增持"}, "llm_used": True}
    rc.save_report("600000", "2026-07-06", rep)
    got = rc.read_report("600000")
    assert got["verdict"]["stance"] == "买入/增持"


def test_read_report_latest_as_of():
    rc.save_report("600000", "2026-07-05", {"v": 1})
    rc.save_report("600000", "2026-07-06", {"v": 2})
    assert rc.read_report("600000")["v"] == 2
