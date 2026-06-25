def test_weights_presets(client):
    r = client.get("/api/quant/weights")
    assert r.status_code == 200
    body = r.json()
    assert "ic" in body and "momentum" in body and isinstance(body["ic"], dict)


def test_backtest_submit_then_poll(client, seed_db):
    r = client.post("/api/quant/backtest", json={"weights": "ic", "top_n": 2, "rebalance_every": 5, "min_history": 60})
    assert r.status_code == 200
    jid = r.json()["job_id"]
    g = client.get(f"/api/quant/backtest/{jid}")
    assert g.status_code == 200
    body = g.json()
    assert body["status"] == "done"          # 同步模式提交即完成
    assert "metrics" in body["result"] and "nav" in body["result"]


def test_factor_ic_submit_then_poll(client, seed_db):
    r = client.post("/api/quant/factor-ic", json={"factors": ["mom_20", "volatility_20"], "fwd": 5})
    jid = r.json()["job_id"]
    body = client.get(f"/api/quant/factor-ic/{jid}").json()
    assert body["status"] == "done"
    assert "rows" in body["result"]


def test_unknown_job_404(client):
    assert client.get("/api/quant/backtest/nosuch").status_code == 404
