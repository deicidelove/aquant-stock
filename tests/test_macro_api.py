import pandas as pd


def test_indices_endpoint(client, seed_db, monkeypatch):
    from aquant import macro
    monkeypatch.setattr(macro, "indices", lambda codes=None: [{"code": "sh000300", "close": 3900.0}])
    r = client.get("/api/cockpit/indices")
    assert r.status_code == 200 and r.json()["rows"][0]["code"] == "sh000300"


def test_sentiment_endpoint(client, seed_db):
    r = client.get("/api/cockpit/sentiment")
    assert r.status_code == 200
    assert "score" in r.json() and "label" in r.json()


def test_sector_fund_endpoint(client, seed_db):
    seed_db.save("sector_fund_flow", pd.DataFrame([
        {"sector": "医药", "pct_chg": 2.0, "main_net": 5e8, "main_net_pct": 1.0, "leader": "恒瑞", "date": "2026-06-23"}]))
    r = client.get("/api/cockpit/sector-fund")
    assert r.status_code == 200 and r.json()["rows"][0]["sector"] == "医药"


def test_abnormal_endpoint(client, seed_db):
    r = client.get("/api/cockpit/abnormal?scope=sector&n=5&z=2")
    assert r.status_code == 200 and r.json()["scope"] == "sector"
