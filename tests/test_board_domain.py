import pandas as pd
import pytest

from aquant.data import store
from aquant import board


@pytest.fixture()
def seed_limit():
    store.save("limit_pool", pd.DataFrame([
        {"code": "000001", "name": "龙头A", "date": "2026-07-03", "pct_chg": 10.0, "amount": 5e8,
         "turnover": 8.0, "seal_fund": 3e8, "break_times": 0, "boards": 3, "industry": "半导体", "first_seal_time": "093000"},
        {"code": "000002", "name": "龙头B", "date": "2026-07-03", "pct_chg": 10.0, "amount": 3e8,
         "turnover": 6.0, "seal_fund": 2e8, "break_times": 2, "boards": 2, "industry": "半导体", "first_seal_time": "100000"},
        {"code": "000003", "name": "普通C", "date": "2026-07-03", "pct_chg": 10.0, "amount": 1e8,
         "turnover": 5.0, "seal_fund": 1e8, "break_times": 0, "boards": 1, "industry": "医药", "first_seal_time": "110000"},
    ]))
    return store


def test_limit_ladder(seed_limit):
    r = board.limit_ladder()
    assert r["date"] == "2026-07-03"
    assert r["limit_up_count"] == 3
    assert r["max_boards"] == 3
    # 梯队按连板数降序
    boards_order = [x["boards"] for x in r["ladder"]]
    assert boards_order == [3, 2, 1]
    # 3板组含龙头A
    top = next(x for x in r["ladder"] if x["boards"] == 3)
    assert "龙头A" in top["names"]
    # 行业分布含半导体2
    semi = next(x for x in r["by_industry"] if x["industry"] == "半导体")
    assert semi["count"] == 2


def test_north_flow(seed_limit):
    store.save("north_flow", pd.DataFrame([
        {"date": "2026-07-03", "market": "沪股通", "net": 12.3},
        {"date": "2026-07-03", "market": "深股通", "net": -4.5},
    ]))
    r = board.north_flow()
    assert r["date"] == "2026-07-03"
    markets = {x["market"]: x["net"] for x in r["rows"]}
    assert markets["沪股通"] == 12.3


def test_empty_no_crash():
    assert board.limit_ladder()["ladder"] == []
    assert board.north_flow()["rows"] == []
