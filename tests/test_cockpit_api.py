def test_overview(client, monkeypatch):
    from aquant import market
    monkeypatch.setattr(market, "breadth", lambda: {"up": 2500, "down": 1800})
    monkeypatch.setattr(market, "regime", lambda: {"state": "均衡", "score": 0.5})
    monkeypatch.setattr(market, "index_trend", lambda code="sh000300": {"code": code, "close": 3900.0})
    r = client.get("/api/cockpit/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["breadth"]["up"] == 2500
    assert body["regime"]["state"] == "均衡"
    assert body["index"]["close"] == 3900.0
