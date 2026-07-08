import pandas as pd

from aquant.data import store


def test_margin_endpoint(client):
    store.save("margin_balance", pd.DataFrame([
        {"date": "2026-07-07", "market": "sh", "fin_balance": 1.5e12, "total_balance": 1.53e12},
        {"date": "2026-07-07", "market": "sz", "fin_balance": 1.1e12, "total_balance": 1.11e12},
    ]))
    r = client.get("/api/cockpit/margin")
    assert r.status_code == 200
    b = r.json()
    assert b["date"] == "2026-07-07"
    assert round(b["total_fin"]) == 26000


def test_block_trade_endpoint(client):
    store.save("block_trade", pd.DataFrame([
        {"date": "2026-07-07", "total_amount": 5e9, "premium_amount": 2e9, "discount_amount": 3e9, "premium_ratio": 0.4},
    ]))
    r = client.get("/api/cockpit/block-trade")
    assert r.status_code == 200
    assert r.json()["rows"][0]["date"] == "2026-07-07"


def test_margin_empty_ok(client):
    r = client.get("/api/cockpit/margin")
    assert r.status_code == 200
    assert r.json()["series"] == []
