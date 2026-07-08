import pandas as pd

from aquant.data import store
from server.refresh import board_data as rb


def test_refresh_limit_pool(monkeypatch):
    fake = pd.DataFrame([
        {"code": "000001", "name": "A", "pct_chg": 10.0, "amount": 1e8, "turnover": 5.0,
         "seal_fund": 2e8, "break_times": 0, "boards": 2, "industry": "半导体", "first_seal_time": "0930"},
    ])
    monkeypatch.setattr(rb.src, "limit_pool", lambda date: fake)
    n = rb.refresh_limit_pool()
    assert n == 1
    d = store.query("SELECT boards,industry,date FROM limit_pool WHERE code='000001'")
    assert d["boards"].iloc[0] == 2
    assert d["date"].iloc[0]  # 已填当日


def test_refresh_north(monkeypatch):
    fake = pd.DataFrame([{"market": "沪股通", "net": 12.3}, {"market": "深股通", "net": -4.5}])
    monkeypatch.setattr(rb.src, "north_summary", lambda: fake)
    n = rb.refresh_north()
    assert n == 2
    d = store.query("SELECT market,net,date FROM north_flow WHERE market='沪股通'")
    assert d["net"].iloc[0] == 12.3


def test_refresh_empty_ok(monkeypatch):
    monkeypatch.setattr(rb.src, "limit_pool", lambda date: pd.DataFrame())
    assert rb.refresh_limit_pool() == 0
