from aquant import analysts


def test_ai_report_generate_and_read(client, monkeypatch):
    canned = {"code": "600000", "name": "浦发银行", "as_of": "2026-07-06",
              "analysts": {"technical": "多头", "capital": "机构进场",
                           "news": "利好", "fundamental": "估值合理"},
              "debate": {"bull": "看多", "bear": "看空"},
              "verdict": {"stance": "买入/增持", "reason": "x", "position": "5成", "risks": ["无"]},
              "llm_used": True}
    monkeypatch.setattr(analysts, "ai_research", lambda code, offline=False: canned)

    # 生成前缓存为空
    assert client.get("/api/stock/600000/ai-report").json()["report"] is None

    # 触发（AQUANT_JOBS_SYNC=1 同步执行）
    r = client.post("/api/stock/600000/ai-report")
    assert r.status_code == 200 and r.json()["job_id"]

    got = client.get("/api/stock/600000/ai-report").json()["report"]
    assert got is not None
    assert got["verdict"]["stance"] == "买入/增持"
    assert set(got["analysts"]) == {"technical", "capital", "news", "fundamental"}
