import pandas as pd

from aquant.data import store


def test_news_sentiment_endpoint(client):
    store.save("market_news", pd.DataFrame([
        {"time": "2026-07-05 09:00", "title": "央行降准", "summary": "利好", "url": "http://a", "sent": 1},
        {"time": "2026-07-05 08:30", "title": "某股立案", "summary": "监管", "url": "http://b", "sent": -1},
        {"time": "2026-07-05 08:00", "title": "行情播报", "summary": "", "url": "http://c", "sent": 0},
    ]))
    r = client.get("/api/cockpit/news-sentiment?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["pos"] == 1 and body["neg"] == 1 and body["neutral"] == 1
    assert 0 <= body["score"] <= 100
    assert len(body["items"]) == 3
    assert body["items"][0]["title"] == "央行降准"  # 按时间降序


def test_news_sentiment_empty_ok(client):
    r = client.get("/api/cockpit/news-sentiment")
    assert r.status_code == 200
    assert r.json()["items"] == []
