def test_materialize_then_read(seed_db):
    from server.refresh import scores
    n = scores.materialize_scores()
    assert n >= 2  # 至少 2 只 fixture 股票被打分
    top = scores.read_top_scores(top=1)
    assert len(top) == 1
    assert set(["code", "name", "score", "as_of"]).issubset(top.columns)
    assert top["as_of"].iloc[0] == "2026-04-22"  # daily_bar 最新日
