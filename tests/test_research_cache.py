def test_news_roundtrip(seed_db):
    from aquant.data import research_cache as rc
    items = [{"title": "公司中标大单", "time": "2026-06-23 09:00:00", "source": "东财"}]
    n = rc.save_news("600000", "2026-06-23", items)
    assert n == 1
    assert rc.read_news("600000") == items
    assert rc.read_news("000001") == []  # 未缓存 → 空


def test_context_roundtrip(seed_db):
    from aquant.data import research_cache as rc
    ctx = {"valuation": {"pe": 5.1}, "financial": {"roe": 12.3},
           "chip": {"profit_ratio": 0.8}, "dividend": {"dividend_yield": 3.2}}
    rc.save_context("600000", "2026-06-23", ctx)
    assert rc.read_context("600000") == ctx
    assert rc.read_context("000001") == {}
