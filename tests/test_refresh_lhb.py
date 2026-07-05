import pandas as pd

from aquant.data import store
from server.refresh import lhb as rlhb


def test_refresh_lhb_ingests_detail_and_seats(monkeypatch):
    detail = pd.DataFrame([
        {"code": "600000", "name": "浦发银行", "date": "2026-07-03", "reason": "涨幅偏离",
         "close": 10.0, "pct_chg": 9.9, "lhb_net_buy": 5e7, "lhb_amount": 2e8},
    ])
    buy = pd.DataFrame([
        {"rank": 1, "seat": "机构专用", "buy": 3e7, "sell": 0.0, "net": 3e7},
    ])
    sell = pd.DataFrame([
        {"rank": 1, "seat": "平安证券某营业部", "buy": 0.0, "sell": 1e7, "net": -1e7},
    ])
    monkeypatch.setattr(rlhb.src, "lhb_detail", lambda start, end: detail)
    monkeypatch.setattr(rlhb.src, "lhb_seats",
                        lambda code, date, flag: buy if flag == "买入" else sell)

    n = rlhb.refresh_lhb(days=1)
    assert n >= 1

    d = store.query("SELECT * FROM lhb_detail WHERE code='600000'")
    assert len(d) == 1
    s = store.query("SELECT side,seat_type,net FROM lhb_seat WHERE code='600000' ORDER BY side")
    assert set(s["side"]) == {"buy", "sell"}
    assert (s[s["side"] == "buy"]["seat_type"] == "inst").all()
    assert (s[s["side"] == "sell"]["net"] < 0).all()


def test_refresh_lhb_null_reason_ok(monkeypatch):
    # 真实数据 reason 可能为空，reason 是主键 NOT NULL，须填充
    detail = pd.DataFrame([
        {"code": "600001", "name": "X", "date": "2026-07-03", "reason": None,
         "close": 1.0, "pct_chg": 1.0, "lhb_net_buy": 1e7, "lhb_amount": 2e7},
    ])
    monkeypatch.setattr(rlhb.src, "lhb_detail", lambda start, end: detail)
    monkeypatch.setattr(rlhb.src, "lhb_seats", lambda code, date, flag: pd.DataFrame())
    rlhb.refresh_lhb(days=1)
    d = store.query("SELECT reason FROM lhb_detail WHERE code='600001'")
    assert d["reason"].iloc[0] == ""
