from aquant.data import store
from server.refresh import news as rnews


def test_refresh_market_news_scores_and_saves(monkeypatch):
    fake = [
        {"title": "央行降准释放流动性", "summary": "利好", "time": "2026-07-05 09:00", "url": "http://a"},
        {"title": "某公司被立案调查", "summary": "监管", "time": "2026-07-05 08:30", "url": "http://b"},
        {"title": "午间收盘播报", "summary": "行情", "time": "2026-07-05 11:30", "url": "http://c"},
    ]
    monkeypatch.setattr(rnews.src, "market_news", lambda limit=50: fake)
    n = rnews.refresh_market_news()
    assert n == 3
    df = store.query("SELECT title,sent FROM market_news ORDER BY time")
    smap = dict(zip(df["title"], df["sent"]))
    assert smap["央行降准释放流动性"] == 1
    assert smap["某公司被立案调查"] == -1
    assert smap["午间收盘播报"] == 0


def test_refresh_empty_ok(monkeypatch):
    monkeypatch.setattr(rnews.src, "market_news", lambda limit=50: [])
    assert rnews.refresh_market_news() == 0
