import pandas as pd

from aquant.data.sources import akshare_source as s


def test_margin_sse_maps(monkeypatch):
    fake = pd.DataFrame([
        {"信用交易日期": "20260702", "融资余额": 1.5e12, "融资买入额": 1e11,
         "融券余量": 2e9, "融券余量金额": 1e10, "融券卖出量": 6e7, "融资融券余额": 1.53e12},
    ])
    monkeypatch.setattr(s.ak, "stock_margin_sse", lambda start_date, end_date: fake)
    df = s.margin_sse("20260701", "20260708")
    assert set(["date", "fin_balance", "total_balance"]).issubset(df.columns)
    assert df["date"].iloc[0] == "2026-07-02"
    assert df["fin_balance"].iloc[0] == 1.5e12


def test_margin_szse_maps(monkeypatch):
    fake = pd.DataFrame([
        {"融资买入额": 1e11, "融资余额": 1.1e12, "融券卖出量": 5e7,
         "融券余量": 1e9, "融券余额": 8e9, "融资融券余额": 1.11e12},
    ])
    monkeypatch.setattr(s.ak, "stock_margin_szse", lambda date: fake)
    df = s.margin_szse("2026-07-07")
    assert df["date"].iloc[0] == "2026-07-07"
    assert df["total_balance"].iloc[0] == 1.11e12


def test_block_trade_stat_maps(monkeypatch):
    fake = pd.DataFrame([
        {"交易日期": "2026-07-07", "大宗交易成交总额": 5e9, "溢价成交总额": 2e9,
         "溢价成交总额占比": 0.4, "折价成交总额": 3e9},
        {"交易日期": "2026-07-06", "大宗交易成交总额": 4e9, "溢价成交总额": 1e9,
         "溢价成交总额占比": 0.25, "折价成交总额": 3e9},
    ])
    monkeypatch.setattr(s.ak, "stock_dzjy_sctj", lambda: fake)
    df = s.block_trade_stat()
    assert set(["date", "total_amount", "premium_amount", "discount_amount", "premium_ratio"]).issubset(df.columns)
    assert df["date"].iloc[0] == "2026-07-07"
