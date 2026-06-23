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


def test_refresh_sectors_writes_rows(seed_db):
    from server.refresh import snapshots
    fake = pd.DataFrame({"sector": ["银行", "煤炭"], "pct_chg": [1.1, -0.3],
                         "mkt_cap": [5e11, 2e11]})
    n = snapshots.refresh_sectors(fetch=lambda: fake)
    assert n == 2
    rows = seed_db.query("SELECT sector, ts FROM sector_snapshot ORDER BY sector")
    assert set(rows["sector"]) == {"银行", "煤炭"}
    assert rows["ts"].notna().all()
