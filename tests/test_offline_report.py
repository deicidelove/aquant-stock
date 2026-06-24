def test_stock_report_offline_reads_cache(seed_db, monkeypatch):
    from aquant import research
    from aquant.data import research_cache as rc
    from aquant.data.sources import news as news_mod
    from aquant.data.sources import fundamental as fund

    rc.save_news("600000", "2026-04-22", [{"title": "离线缓存新闻", "time": "2026-04-22", "source": "东财"}])
    rc.save_context("600000", "2026-04-22",
                    {"valuation": {"pe": 5.0}, "financial": {}, "chip": {}, "dividend": {}})

    # 离线路径绝不调用实时抓取：调用即让测试失败
    def _boom(*a, **k):
        raise AssertionError("offline 路径不应触网")
    monkeypatch.setattr(news_mod, "stock_news", _boom)
    monkeypatch.setattr(fund, "context", _boom)

    rep = research.stock_report("600000", offline=True)
    assert rep
    assert rep["news"] == [{"title": "离线缓存新闻", "time": "2026-04-22", "source": "东财"}]
    assert rep["fundamental"]["valuation"]["pe"] == 5.0
