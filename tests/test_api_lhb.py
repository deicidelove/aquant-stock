import pandas as pd

from aquant.data import store


def _seed():
    store.save("lhb_detail", pd.DataFrame([
        {"code": "600000", "name": "浦发银行", "date": "2026-07-03", "reason": "涨幅偏离",
         "close": 10.0, "pct_chg": 9.9, "lhb_net_buy": 5e7, "lhb_amount": 2e8},
        {"code": "000001", "name": "平安银行", "date": "2026-07-03", "reason": "换手",
         "close": 20.0, "pct_chg": 3.0, "lhb_net_buy": 1e7, "lhb_amount": 1e8},
    ]))
    store.save("lhb_seat", pd.DataFrame([
        {"code": "600000", "date": "2026-07-03", "side": "buy", "rank": 1, "seat": "机构专用",
         "buy": 3e7, "sell": 0.0, "net": 3e7, "seat_type": "inst", "hotmoney_name": None},
        {"code": "600000", "date": "2026-07-03", "side": "sell", "rank": 1, "seat": "平安某部",
         "buy": 0.0, "sell": 1e7, "net": -1e7, "seat_type": "normal", "hotmoney_name": None},
    ]))


def test_today_sorted(client):
    _seed()
    r = client.get("/api/lhb/today")
    assert r.status_code == 200
    body = r.json()
    assert body["date"] == "2026-07-03"
    assert [x["code"] for x in body["rows"]] == ["600000", "000001"]
    assert "机构" in body["rows"][0]["tags"]


def test_stock_seats(client):
    _seed()
    r = client.get("/api/lhb/stock/600000")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "浦发银行"
    assert len(body["buy"]) == 1 and len(body["sell"]) == 1
    assert body["buy"][0]["seat_type"] == "inst"


def test_today_empty_ok(client):
    # 无 lhb 数据也应 200（请求路径不发网络）
    r = client.get("/api/lhb/today")
    assert r.status_code == 200
    assert r.json()["rows"] == []
