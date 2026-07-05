def test_stock_chart_shape(seed_db):
    from aquant import chart
    out = chart.stock_chart("600000", n=30)
    assert out["code"] == "600000"
    assert len(out["bars"]) == 30
    b = out["bars"][0]
    assert set(["date", "open", "high", "low", "close", "volume"]) == set(b)
    for k in ("ma5", "ma10", "ma20", "ma60"):
        assert len(out["ma"][k]) == 30
    for k in ("dif", "dea", "hist"):
        assert len(out["macd"][k]) == 30
    # fixture 80 日 → 尾段(末=第80日) MA60 有值
    assert out["ma"]["ma60"][-1] is not None
    # tail(30) 首行=第51日 < 60 → MA60 不足窗口为 None
    assert out["ma"]["ma60"][0] is None


def test_stock_chart_empty(seed_db):
    from aquant import chart
    out = chart.stock_chart("999999", n=30)
    assert out["bars"] == [] and out["macd"]["dif"] == []
