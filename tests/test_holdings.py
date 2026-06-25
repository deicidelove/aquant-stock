import pandas as pd


def test_record_list_delete_trade(seed_db):
    from aquant.portfolio import holdings
    t1 = holdings.record_trade("2026-02-02", "600000", "buy", 1000, 10.0)
    t2 = holdings.record_trade("2026-02-03", "600000", "buy", 1000, 12.0)
    assert (t1, t2) == (1, 2)
    df = holdings.list_trades()
    assert len(df) == 2 and list(df["tid"]) == [1, 2]
    assert holdings.delete_trade(1) == 1
    assert list(holdings.list_trades()["tid"]) == [2]


def test_holdings_aggregation_and_pnl(seed_db):
    from aquant.portfolio import holdings
    # 600000 fixture 最新收盘 = 10 + 79*0.05 = 13.95
    holdings.record_trade("2026-02-02", "600000", "buy", 1000, 10.0)
    holdings.record_trade("2026-02-03", "600000", "buy", 1000, 12.0)  # 加权成本 11.0
    holdings.record_trade("2026-02-10", "600000", "sell", 500, 13.0)  # 已实现 (13-11)*500=1000
    pos = {h["code"]: h for h in holdings.holdings()}
    assert "600000" in pos
    h = pos["600000"]
    assert h["shares"] == 1500
    assert round(h["avg_cost"], 4) == 11.0
    assert h["last_price"] == 13.95
    assert round(h["unrealized"], 2) == round((13.95 - 11.0) * 1500, 2)
    s = holdings.pnl_summary()
    assert round(s["realized"], 2) == 1000.0
    assert round(s["total"], 2) == round(s["realized"] + s["unrealized"], 2)
