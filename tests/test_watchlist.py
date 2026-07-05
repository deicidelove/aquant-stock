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
