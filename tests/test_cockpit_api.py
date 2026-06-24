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


import pandas as pd


def test_sectors(client, seed_db, monkeypatch):
    from server.refresh import snapshots
    from aquant import sector
    snapshots.refresh_sectors(fetch=lambda: pd.DataFrame(
        {"sector": ["银行", "煤炭"], "pct_chg": [1.1, -0.3], "mkt_cap": [5e11, 2e11]}))
    monkeypatch.setattr(sector, "rotation", lambda top=10: {"leaders": ["银行"]})
    r = client.get("/api/cockpit/sectors")
    assert r.status_code == 200
    body = r.json()
    assert body["rows"][0]["sector"] == "银行"      # pct_chg 最高在前
    assert body["rotation"]["leaders"] == ["银行"]


def test_top_scores(client, seed_db):
    from server.refresh import scores
    scores.materialize_scores()
    r = client.get("/api/cockpit/top-scores?top=1")
    assert r.status_code == 200
    body = r.json()
    assert len(body["rows"]) == 1
    assert "score" in body["rows"][0]


def test_picks(client, seed_db, monkeypatch):
    import pandas as pd
    from aquant import research
    monkeypatch.setattr(research, "daily_picks",
                        lambda **k: pd.DataFrame([{"code": "600000", "name": "浦发", "score": 1.2}]))
    r = client.get("/api/cockpit/picks?top=3")
    assert r.status_code == 200
    assert r.json()["rows"][0]["code"] == "600000"
