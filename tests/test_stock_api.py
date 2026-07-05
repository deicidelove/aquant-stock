def test_kline(client, seed_db):
    r = client.get("/api/stock/600000/kline?n=10")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "600000"
    assert len(body["bars"]) == 10
    assert {"date", "open", "high", "low", "close", "volume"} <= set(body["bars"][0])


def test_report_offline(client, seed_db, monkeypatch):
    from aquant.data import research_cache as rc
    from aquant.data.sources import news as news_mod
    from aquant.data.sources import fundamental as fund
    rc.save_news("600000", "2026-04-22", [{"title": "缓存新闻", "time": "2026-04-22", "source": "东财"}])
    rc.save_context("600000", "2026-04-22", {"valuation": {}, "financial": {}, "chip": {}, "dividend": {}})
    monkeypatch.setattr(news_mod, "stock_news", lambda *a, **k: (_ for _ in ()).throw(AssertionError("不应触网")))
    monkeypatch.setattr(fund, "context", lambda *a, **k: (_ for _ in ()).throw(AssertionError("不应触网")))
    r = client.get("/api/stock/600000/report")
    assert r.status_code == 200
    assert r.json()["code"] == "600000"
    assert r.json()["decision"]


def test_chart_endpoint(client, seed_db):
    r = client.get("/api/stock/600000/chart?n=20")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "600000"
    assert len(body["bars"]) == 20
    assert set(["ma5", "ma10", "ma20", "ma60"]).issubset(body["ma"])
    assert set(["dif", "dea", "hist"]).issubset(body["macd"])
