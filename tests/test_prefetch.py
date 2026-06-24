def test_prefetch_writes_cache(seed_db, monkeypatch):
    from server.refresh import research_cache as pf
    from aquant.data import research_cache as rc

    # 限定 universe 为 fixture 里的 code，避免依赖打分结果
    monkeypatch.setattr(pf, "prefetch_universe", lambda top=120: ["600000"])
    news = [{"title": "中标", "time": "2026-06-23", "source": "东财"}]
    ctx = {"valuation": {"pe": 5.0}, "financial": {}, "chip": {}, "dividend": {}}

    n = pf.prefetch_research(news_fetch=lambda c: news, ctx_fetch=lambda c: ctx)
    assert n == 1
    assert rc.read_news("600000") == news
    assert rc.read_context("600000") == ctx


def test_prefetch_universe_union(seed_db, monkeypatch):
    from server.refresh import research_cache as pf
    import pandas as pd
    from server.refresh import scores
    from aquant import research
    monkeypatch.setattr(scores, "read_top_scores",
                        lambda top=120: pd.DataFrame({"code": ["600000"], "name": ["x"],
                                                      "score": [1.0], "as_of": ["2026-06-23"]}))
    monkeypatch.setattr(research, "daily_picks",
                        lambda **k: pd.DataFrame({"code": ["000001"], "name": ["y"], "score": [2.0]}))
    assert pf.prefetch_universe() == ["000001", "600000"]
