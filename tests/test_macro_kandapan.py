import pandas as pd


def test_regime_passthrough(seed_db, monkeypatch):
    from aquant import macro, market
    monkeypatch.setattr(market, "regime", lambda: {"state": "防守", "score": 1, "suggested_position": "1~3成", "note": "x"})
    assert macro.regime()["state"] == "防守"


def test_index_series(seed_db):
    from aquant import macro
    # 注入指数收盘序列（70 日，够算 MA20 与 MA60）
    dates = pd.bdate_range("2026-01-01", periods=70).strftime("%Y-%m-%d").tolist()
    seed_db.save("index_daily", pd.DataFrame([
        {"code": "sh000300", "date": d, "close": 3900 + i} for i, d in enumerate(dates)]))
    out = macro.index_series("sh000300", n=30)
    assert out["code"] == "sh000300"
    assert len(out["points"]) == 30
    p = out["points"][-1]
    assert set(["date", "close", "ma20", "ma60"]).issubset(p)
    assert p["ma20"] is not None            # 70>=20
    assert p["ma60"] is not None            # 70>=60


def test_amount_trend(seed_db):
    from aquant import macro
    # seed_db 的 daily_bar 有 amount（2 只×80 日）
    out = macro.amount_trend(days=5)
    assert isinstance(out["series"], list) and len(out["series"]) == 5
    assert set(["date", "amount"]).issubset(out["series"][0])
