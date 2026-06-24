def test_kline(client, seed_db):
    r = client.get("/api/stock/600000/kline?n=10")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "600000"
    assert len(body["bars"]) == 10
    assert {"date", "open", "high", "low", "close", "volume"} <= set(body["bars"][0])


def test_report(client, seed_db, monkeypatch):
    from aquant import research
    monkeypatch.setattr(research, "decision", lambda code, rep=None: {"code": code, "signal": "持有/观望"})
    r = client.get("/api/stock/600000/report")
    assert r.status_code == 200
    assert r.json()["decision"]["signal"] == "持有/观望"
