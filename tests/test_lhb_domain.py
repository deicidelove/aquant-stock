import pandas as pd
import pytest

from aquant.data import store
from aquant import lhb


@pytest.fixture()
def seed_lhb():
    store.save("lhb_detail", pd.DataFrame([
        {"code": "600000", "name": "浦发银行", "date": "2026-07-03", "reason": "日涨幅偏离7%",
         "close": 10.0, "pct_chg": 9.9, "lhb_net_buy": 5e7, "lhb_amount": 2e8},
        {"code": "000001", "name": "平安银行", "date": "2026-07-03", "reason": "换手率20%",
         "close": 20.0, "pct_chg": 3.0, "lhb_net_buy": 1e7, "lhb_amount": 1e8},
    ]))
    store.save("lhb_seat", pd.DataFrame([
        {"code": "600000", "date": "2026-07-03", "side": "buy", "rank": 1,
         "seat": "机构专用", "buy": 3e7, "sell": 0.0, "net": 3e7,
         "seat_type": "inst", "hotmoney_name": None},
        {"code": "600000", "date": "2026-07-03", "side": "buy", "rank": 2,
         "seat": "中国银河证券股份有限公司绍兴证券营业部", "buy": 2e7, "sell": 0.0, "net": 2e7,
         "seat_type": "hotmoney", "hotmoney_name": "章盟主"},
        {"code": "600000", "date": "2026-07-03", "side": "sell", "rank": 1,
         "seat": "平安证券某营业部", "buy": 0.0, "sell": 1e7, "net": -1e7,
         "seat_type": "normal", "hotmoney_name": None},
    ]))
    return store


def test_today_sorted_desc_with_tags(seed_lhb):
    r = lhb.lhb_today()
    assert r["date"] == "2026-07-03"
    rows = r["rows"]
    assert [x["code"] for x in rows] == ["600000", "000001"]  # 按净买额降序
    top = rows[0]
    assert "机构" in top["tags"]
    assert "章盟主" in top["tags"]


def test_stock_detail(seed_lhb):
    r = lhb.lhb_stock("600000")
    assert r["name"] == "浦发银行"
    assert r["date"] == "2026-07-03"
    assert len(r["buy"]) == 2 and len(r["sell"]) == 1
    assert r["buy"][0]["seat_type"] == "inst"
    assert r["sell"][0]["net"] == -1e7


def test_empty_no_crash():
    assert lhb.lhb_today()["rows"] == []
    r = lhb.lhb_stock("999999")
    assert r["buy"] == [] and r["sell"] == []
