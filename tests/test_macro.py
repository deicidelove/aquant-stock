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


def test_sector_fund_rank(seed_db):
    from aquant import macro
    seed_db.save("sector_fund_flow", pd.DataFrame([
        {"sector": "医药", "pct_chg": 2.0, "main_net": 5e8, "main_net_pct": 1.0, "leader": "恒瑞", "date": "2026-06-23"},
        {"sector": "煤炭", "pct_chg": -1.0, "main_net": -2e8, "main_net_pct": -1.0, "leader": "神华", "date": "2026-06-23"},
    ]))
    r = macro.sector_fund_rank()
    assert r["as_of"] == "2026-06-23"
    assert r["rows"][0]["sector"] == "医药"  # main_net 降序


def test_abnormal_fund_stock(seed_db):
    from aquant import macro
    # 600000 近几日 main_net 平稳但有小波动，最新一日暴增 → 异常
    rows = []
    for i, d in enumerate(["2026-06-17", "2026-06-18", "2026-06-19", "2026-06-22"]):
        # 近3日分别为 1e7, 2e7, 1.5e7 (平均1.5e7), 最新日暴增到 5e8
        main_net_val = [1e7, 2e7, 1.5e7, 5e8][i]
        rows.append({"code": "600000", "name": "浦发", "close": 10, "pct_chg": 1,
                     "main_net": main_net_val, "main_net_pct": 1, "date": d})
    seed_db.save("fund_flow", pd.DataFrame(rows))
    out = macro.abnormal_fund(scope="stock", n=5, z=2.0)
    assert out["scope"] == "stock"
    assert any(x["key"] == "600000" for x in out["rows"])
