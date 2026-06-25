import pandas as pd


def test_briefing_endpoint_offline(client, monkeypatch):
    import aquant.research as research
    called = {}
    def fake_briefing(top=12, weights=None, offline=False):
        called["offline"] = offline
        return pd.DataFrame([{"code": "600000", "name": "浦发", "综合分": 1.2, "信号": "买入/增持"}])
    monkeypatch.setattr(research, "briefing", fake_briefing)
    r = client.get("/api/assist/briefing?top=5")
    assert r.status_code == 200
    assert r.json()["rows"][0]["code"] == "600000"
    assert called["offline"] is True  # 端点必须以离线调用，守住不联网铁律


def test_scorecard_endpoint(client, monkeypatch):
    from aquant.track import evaluate
    monkeypatch.setattr(evaluate, "forward_returns",
                        lambda: pd.DataFrame([{"as_of": "2026-06-01", "code": "600000", "rank": 1, "fwd_20": 0.03, "exc_20": 0.01}]))
    r = client.get("/api/assist/scorecard")
    assert r.status_code == 200
    body = r.json()
    assert body["as_of"] == "2026-06-01"
    assert body["rows"][0]["exc_20"] == 0.01


def test_scorecard_empty(client, monkeypatch):
    from aquant.track import evaluate
    monkeypatch.setattr(evaluate, "forward_returns", lambda: pd.DataFrame())
    r = client.get("/api/assist/scorecard")
    assert r.status_code == 200
    assert r.json() == {"as_of": None, "rows": []}
