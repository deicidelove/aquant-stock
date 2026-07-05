import pandas as pd

from aquant.data.sources import news as newssrc


def test_market_news_maps_columns(monkeypatch):
    fake = pd.DataFrame([
        {"标题": "央行降准", "摘要": "释放流动性", "发布时间": "2026-07-05 09:00", "链接": "http://x"},
        {"标题": "某股立案", "摘要": "监管", "发布时间": "2026-07-05 08:30", "链接": "http://y"},
    ])
    monkeypatch.setattr(newssrc.ak, "stock_info_global_em", lambda: fake)
    rows = newssrc.market_news(limit=10)
    assert len(rows) == 2
    assert set(["title", "summary", "time", "url"]).issubset(rows[0].keys())
    assert rows[0]["title"] == "央行降准"
