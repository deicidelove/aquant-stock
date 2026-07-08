import pandas as pd

from aquant.data import store
from aquant.track import evaluate


def _seed():
    # 沪深300 日历(基准) 12 天
    dates = pd.bdate_range("2026-01-05", periods=12).strftime("%Y-%m-%d").tolist()
    store.save("index_daily", pd.DataFrame(
        [{"code": "sh000300", "date": d, "close": 4000 + i} for i, d in enumerate(dates)]))
    # 两只个股行情
    rows = []
    for code, base, slope in (("600000", 10.0, 0.5), ("000001", 20.0, -0.2)):
        for i, d in enumerate(dates):
            rows.append({"code": code, "date": d, "close": base + i * slope})
    store.save("daily_bar", pd.DataFrame(rows))
    # 台账：as_of=第0天，两只
    store.save("picks_log", pd.DataFrame([
        {"as_of": dates[0], "code": "600000", "name": "浦发", "rank": 1, "score": 3.5,
         "action": "买入", "signal": "ma_cross", "entry_close": 10.0},
        {"as_of": dates[0], "code": "000001", "name": "平安", "rank": 2, "score": 3.0,
         "action": "买入", "signal": "ma_cross", "entry_close": 20.0},
    ]))
    return dates


def test_scorecard_data_structure():
    dates = _seed()
    d = evaluate.scorecard_data(horizons=(5,))
    assert d["sample"]["picks"] == 2
    assert d["sample"]["snapshots"] == 1
    assert d["sample"]["start"] == dates[0]
    h = d["horizons"][0]
    assert h["h"] == 5
    assert h["settled"] == 2  # 第0天+5 交易日已到期
    assert h["pending"] == 0
    # 600000 T+5 收益 = (10+2.5)/10-1 = 0.25；应为正
    assert h["mean_ret"] is not None
    assert 0 <= h["win_rate"] <= 1
    assert isinstance(d["rank_ic"], list)


def test_scorecard_data_empty():
    d = evaluate.scorecard_data()
    assert d["sample"]["picks"] == 0
    assert d["horizons"] == []
