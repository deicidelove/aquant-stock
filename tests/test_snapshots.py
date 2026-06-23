import pandas as pd


def test_refresh_quotes_writes_rows(seed_db):
    from server.refresh import snapshots
    fake = pd.DataFrame({
        "code": ["600000", "000001"], "name": ["浦发", "平安"],
        "close": [10.1, 20.2], "pct_chg": [1.2, -0.5],
        "turnover": [1.5, 2.0], "amount": [1e8, 2e8],
    })
    n = snapshots.refresh_quotes(fetch=lambda: fake)
    assert n == 2
    rows = seed_db.query("SELECT code, close, ts FROM quote_snapshot ORDER BY code")
    assert set(rows["code"]) == {"000001", "600000"}
    assert rows["ts"].notna().all()
