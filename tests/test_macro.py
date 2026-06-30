import pandas as pd


def _seed_fund_flow(store, rows):
    store.save("fund_flow", pd.DataFrame(rows))


def test_sentiment_shape(seed_db):
    from aquant import macro
    s = macro.sentiment()
    assert set(["up", "down", "limit_up", "limit_down", "amount", "score", "label"]).issubset(s)
    assert 0 <= s["score"] <= 100


def test_market_fund_trend(seed_db):
    from aquant import macro
    _seed_fund_flow(seed_db, [
        {"code": "600000", "name": "浦发", "close": 10, "pct_chg": 1, "main_net": 1e8, "main_net_pct": 1, "date": "2026-06-22"},
        {"code": "000001", "name": "平安", "close": 20, "pct_chg": 1, "main_net": -3e8, "main_net_pct": -1, "date": "2026-06-22"},
        {"code": "600000", "name": "浦发", "close": 10, "pct_chg": 1, "main_net": 2e8, "main_net_pct": 1, "date": "2026-06-23"},
    ])
    t = macro.market_fund_trend(days=10)
    assert "today" in t and isinstance(t["series"], list)
    last = [p for p in t["series"] if p["date"] == "2026-06-23"][0]
    assert round(last["net"], 2) == round(2e8 / 1e8, 2)  # 2 亿


def test_indices_skips_missing(seed_db):
    from aquant import macro
    out = macro.indices(["sh000300", "nope999"])
    assert isinstance(out, list)  # 无数据的跳过，不报错
