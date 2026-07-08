import pandas as pd

from aquant.data import store
from aquant import board


def test_margin_summary():
    store.save("margin_balance", pd.DataFrame([
        {"date": "2026-07-07", "market": "sh", "fin_balance": 1.5e12, "total_balance": 1.53e12},
        {"date": "2026-07-07", "market": "sz", "fin_balance": 1.1e12, "total_balance": 1.11e12},
        {"date": "2026-07-06", "market": "sh", "fin_balance": 1.49e12, "total_balance": 1.52e12},
    ]))
    r = board.margin_summary(days=20)
    assert r["date"] == "2026-07-07"
    # 单位折算为亿：(1.5e12+1.1e12)/1e8 = 26000
    assert round(r["total_fin"]) == 26000
    assert len(r["series"]) == 2  # 两个日期
    assert r["series"][-1]["total_fin"] > r["series"][0]["total_fin"]  # 升序且7号更高


def test_block_trade_recent():
    store.save("block_trade", pd.DataFrame([
        {"date": "2026-07-07", "total_amount": 5e9, "premium_amount": 2e9, "discount_amount": 3e9, "premium_ratio": 0.4},
        {"date": "2026-07-06", "total_amount": 4e9, "premium_amount": 1e9, "discount_amount": 3e9, "premium_ratio": 0.25},
    ]))
    r = board.block_trade_recent(days=10)
    assert len(r["rows"]) == 2
    assert r["rows"][0]["date"] == "2026-07-07"  # 降序
    assert round(r["rows"][0]["total_amount"]) == 50  # 5e9/1e8=50亿
    assert r["rows"][0]["premium_ratio"] == 0.4  # 自算 2e9/5e9


def test_empty_no_crash():
    assert board.margin_summary()["series"] == []
    assert board.block_trade_recent()["rows"] == []
