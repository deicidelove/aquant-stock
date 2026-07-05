def test_add_list_remove(seed_db):
    from aquant.portfolio import watchlist
    watchlist.add("600000")
    watchlist.add("000001")
    watchlist.add("600000")  # 幂等
    assert watchlist.list_codes() == ["600000", "000001"]
    assert watchlist.remove("600000") == 1
    assert watchlist.list_codes() == ["000001"]


def test_watchlist_api(client, seed_db):
    assert client.get("/api/watchlist").json()["codes"] == []
    r = client.post("/api/watchlist", json={"code": "600000"})
    assert r.status_code == 200 and r.json()["codes"] == ["600000"]
    client.post("/api/watchlist", json={"code": "000001"})
    assert client.delete("/api/watchlist/600000").json()["codes"] == ["000001"]


def test_board_union_and_card(seed_db):
    from aquant.portfolio import watchlist, holdings
    watchlist.add("600000")                       # 自选
    holdings.record_trade("2026-02-02", "000001", "buy", 1000, 20.0)  # 持仓
    rows = {r["code"]: r for r in watchlist.board(kline_n=10)}
    assert set(rows) == {"600000", "000001"}      # 自选 ∪ 持仓
    c = rows["600000"]
    assert c["name"] == "浦发银行"
    assert c["last_price"] is not None
    assert len(c["kline"]) == 10 and set(c["kline"][0]) == {"date", "close"}
    assert "signal" in c and isinstance(c["alerts"], list)
    assert set(["ideal_buy", "stop_loss", "take_profit"]).issubset(c["battle_plan"]) or c["battle_plan"] == {}


def test_board_api(client, seed_db):
    from aquant.portfolio import watchlist
    watchlist.add("600000")
    r = client.get("/api/board")
    assert r.status_code == 200
    assert r.json()["rows"][0]["code"] == "600000"
