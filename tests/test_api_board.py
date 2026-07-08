import pandas as pd

from aquant.data import store


def test_limit_ladder_endpoint(client):
    store.save("limit_pool", pd.DataFrame([
        {"code": "000001", "name": "龙头A", "date": "2026-07-03", "pct_chg": 10.0, "amount": 5e8,
         "turnover": 8.0, "seal_fund": 3e8, "break_times": 0, "boards": 3, "industry": "半导体", "first_seal_time": "0930"},
        {"code": "000003", "name": "C", "date": "2026-07-03", "pct_chg": 10.0, "amount": 1e8,
         "turnover": 5.0, "seal_fund": 1e8, "break_times": 1, "boards": 1, "industry": "医药", "first_seal_time": "1100"},
    ]))
    r = client.get("/api/cockpit/limit-ladder")
    assert r.status_code == 200
    b = r.json()
    assert b["limit_up_count"] == 2 and b["max_boards"] == 3
    assert b["ladder"][0]["boards"] == 3


def test_north_flow_endpoint(client):
    store.save("north_flow", pd.DataFrame([
        {"date": "2026-07-03", "market": "沪股通", "net": 12.3},
    ]))
    r = client.get("/api/cockpit/north-flow")
    assert r.status_code == 200
    assert r.json()["rows"][0]["market"] == "沪股通"


def test_limit_ladder_empty_ok(client):
    r = client.get("/api/cockpit/limit-ladder")
    assert r.status_code == 200
    assert r.json()["ladder"] == []
