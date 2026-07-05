from aquant import sentiment as s


def test_score_text():
    assert s.score_text("央行宣布降准，释放流动性") == 1
    assert s.score_text("某公司被立案调查") == -1
    assert s.score_text("今日天气晴") == 0


def test_aggregate_bullish():
    items = [{"sent": 1}, {"sent": 1}, {"sent": 1}, {"sent": -1}, {"sent": 0}]
    r = s.aggregate(items)
    assert r["pos"] == 3 and r["neg"] == 1 and r["neutral"] == 1
    assert r["score"] > 50  # 偏多
    assert r["label"]


def test_aggregate_empty():
    r = s.aggregate([])
    assert r["score"] == 50 and r["pos"] == 0 and r["label"]
