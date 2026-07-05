import pandas as pd

from aquant.data.sources import akshare_source as s


def test_lhb_seats_maps_columns(monkeypatch):
    fake = pd.DataFrame([
        {"序号": 1, "交易营业部名称": "机构专用", "买入金额": 3e7,
         "买入金额-占总成交比例": 0.2, "卖出金额": 0.0, "卖出金额-占总成交比例": 0.0,
         "净额": 3e7, "类型": "普通"},
    ])
    monkeypatch.setattr(s.ak, "stock_lhb_stock_detail_em", lambda **k: fake)
    df = s.lhb_seats("600000", "2026-07-03", "买入")
    assert set(["seat", "buy", "sell", "net", "rank"]).issubset(df.columns)
    assert df["seat"].iloc[0] == "机构专用"
    assert df["net"].iloc[0] == 3e7
