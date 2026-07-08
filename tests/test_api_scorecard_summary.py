import pandas as pd

from aquant.data import store


def test_scorecard_summary_endpoint(client):
    dates = pd.bdate_range("2026-01-05", periods=12).strftime("%Y-%m-%d").tolist()
    store.save("index_daily", pd.DataFrame(
        [{"code": "sh000300", "date": d, "close": 4000 + i} for i, d in enumerate(dates)]))
    rows = []
    for code, base, slope in (("600000", 10.0, 0.5), ("000001", 20.0, -0.2)):
        for i, d in enumerate(dates):
            rows.append({"code": code, "date": d, "close": base + i * slope,
                         "open": base, "high": base, "low": base, "volume": 1e6,
                         "amount": base * 1e7, "turnover": 1.0, "pct_chg": 0.0})
    store.save("daily_bar", pd.DataFrame(rows))
    store.save("picks_log", pd.DataFrame([
        {"as_of": dates[0], "code": "600000", "name": "浦发", "rank": 1, "score": 3.5,
         "action": "买入", "signal": "ma_cross", "entry_close": 10.0},
        {"as_of": dates[0], "code": "000001", "name": "平安", "rank": 2, "score": 3.0,
         "action": "买入", "signal": "ma_cross", "entry_close": 20.0},
    ]))
    r = client.get("/api/assist/scorecard-summary")
    assert r.status_code == 200
    b = r.json()
    assert b["sample"]["picks"] == 2
    assert len(b["horizons"]) >= 1
    assert b["horizons"][0]["settled"] >= 1


def test_scorecard_summary_empty(client):
    r = client.get("/api/assist/scorecard-summary")
    assert r.status_code == 200
    assert r.json()["sample"]["picks"] == 0
    assert r.json()["horizons"] == []
