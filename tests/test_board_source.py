import pandas as pd

from aquant.data.sources import akshare_source as s


def test_limit_pool_maps_columns(monkeypatch):
    fake = pd.DataFrame([
        {"代码": "000595", "名称": "宝塔实业", "涨跌幅": 10.0, "成交额": 1e8, "换手率": 5.0,
         "封板资金": 9.3e7, "炸板次数": 0, "连板数": 2, "所属行业": "钢铁", "首次封板时间": "092500"},
    ])
    monkeypatch.setattr(s.ak, "stock_zt_pool_em", lambda date: fake)
    df = s.limit_pool("2026-07-03")
    assert set(["code", "name", "pct_chg", "seal_fund", "break_times", "boards", "industry"]).issubset(df.columns)
    assert df["code"].iloc[0] == "000595"
    assert df["boards"].iloc[0] == 2


def test_north_summary_maps(monkeypatch):
    fake = pd.DataFrame([
        {"类型": "沪港通", "板块": "沪股通", "资金净流入": 12.3},
        {"类型": "深港通", "板块": "深股通", "资金净流入": -4.5},
    ])
    monkeypatch.setattr(s.ak, "stock_hsgt_fund_flow_summary_em", lambda: fake)
    df = s.north_summary()
    assert set(["market", "net"]).issubset(df.columns)
    assert df.loc[df["market"] == "沪股通", "net"].iloc[0] == 12.3
