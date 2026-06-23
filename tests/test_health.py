def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["latest_bar_date"] == "2026-04-22"  # 80 个工作日后的最后一日
