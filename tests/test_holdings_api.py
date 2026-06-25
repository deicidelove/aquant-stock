def test_trade_crud_and_holdings(client, seed_db):
    # 记两笔买入
    r = client.post("/api/holdings/trade", json={"date": "2026-02-02", "code": "600000", "side": "buy", "shares": 1000, "price": 10.0})
    assert r.status_code == 200 and r.json()["tid"] == 1
    client.post("/api/holdings/trade", json={"date": "2026-02-03", "code": "600000", "side": "buy", "shares": 1000, "price": 12.0})
    # 持仓
    h = client.get("/api/holdings").json()["rows"]
    assert len(h) == 1 and h[0]["code"] == "600000" and h[0]["shares"] == 2000
    assert "alerts" in h[0]
    # 盈亏汇总
    pnl = client.get("/api/holdings/pnl").json()
    assert set(pnl) == {"realized", "unrealized", "total"}
    # 流水 + 删除
    assert len(client.get("/api/holdings/trades").json()["rows"]) == 2
    assert client.delete("/api/holdings/trade/1").json()["deleted"] == 1
    assert len(client.get("/api/holdings/trades").json()["rows"]) == 1
