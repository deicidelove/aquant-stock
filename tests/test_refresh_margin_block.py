import pandas as pd

from aquant.data import store
from server.refresh import board_data as rb


def test_refresh_margin(monkeypatch):
    sse = pd.DataFrame([{"date": "2026-07-07", "fin_balance": 1.5e12, "total_balance": 1.53e12}])
    sz = pd.DataFrame([{"date": "2026-07-07", "fin_balance": 1.1e12, "total_balance": 1.11e12}])
    monkeypatch.setattr(rb.src, "margin_sse", lambda start, end: sse)
    monkeypatch.setattr(rb.src, "margin_szse", lambda date: sz)
    n = rb.refresh_margin()
    assert n >= 2
    d = store.query("SELECT market FROM margin_balance WHERE date='2026-07-07' ORDER BY market")
    assert set(d["market"]) == {"sh", "sz"}


def test_refresh_block_trade(monkeypatch):
    fake = pd.DataFrame([
        {"date": "2026-07-07", "total_amount": 5e9, "premium_amount": 2e9, "discount_amount": 3e9, "premium_ratio": 0.4},
    ])
    monkeypatch.setattr(rb.src, "block_trade_stat", lambda: fake)
    n = rb.refresh_block_trade(days=5)
    assert n == 1
    d = store.query("SELECT premium_ratio FROM block_trade WHERE date='2026-07-07'")
    assert d["premium_ratio"].iloc[0] == 0.4


def test_refresh_margin_szse_fail_still_saves_sse(monkeypatch):
    sse = pd.DataFrame([{"date": "2026-07-07", "fin_balance": 1.5e12, "total_balance": 1.53e12}])
    monkeypatch.setattr(rb.src, "margin_sse", lambda start, end: sse)
    monkeypatch.setattr(rb.src, "margin_szse", lambda date: (_ for _ in ()).throw(OSError("down")))
    n = rb.refresh_margin()
    assert n >= 1  # sse 仍入库
    assert not store.query("SELECT * FROM margin_balance WHERE market='sh'").empty
