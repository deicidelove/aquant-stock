import pandas as pd


def test_sector_fund_flow_source_normalizes(monkeypatch):
    from aquant.data.sources import akshare_source as src
    raw = pd.DataFrame({
        "名称": ["医药生物", "煤炭"], "今日涨跌幅": [4.94, -0.8],
        "今日主力净流入-净额": [6.33e9, -1.2e9], "今日主力净流入-净占比": [3.98, -1.0],
        "今日主力净流入最大股": ["恒瑞医药", "中国神华"],
    })
    monkeypatch.setattr(src.ak, "stock_sector_fund_flow_rank", lambda **k: raw)
    df = src.sector_fund_flow()
    assert list(df.columns) == ["sector", "pct_chg", "main_net", "main_net_pct", "leader"]
    assert df.loc[df["sector"] == "医药生物", "main_net"].iloc[0] == 6.33e9


def test_refresh_sector_fund_flow_writes(seed_db):
    from server.refresh import fundflow
    fake = pd.DataFrame({"sector": ["医药生物"], "pct_chg": [4.94], "main_net": [6.33e9],
                         "main_net_pct": [3.98], "leader": ["恒瑞医药"]})
    n = fundflow.refresh_sector_fund_flow(fetch=lambda: fake)
    assert n == 1
    rows = seed_db.query("SELECT sector, main_net, date FROM sector_fund_flow")
    assert rows["sector"].iloc[0] == "医药生物" and rows["date"].notna().all()


def test_refresh_fund_flow_writes(seed_db):
    from server.refresh import fundflow
    fake = pd.DataFrame({"code": ["600000"], "name": ["浦发"], "close": [10.0],
                         "pct_chg": [1.2], "main_net": [1.5e8], "main_net_pct": [3.0]})
    n = fundflow.refresh_fund_flow(fetch=lambda: fake)
    assert n == 1
    rows = seed_db.query("SELECT code, main_net, date FROM fund_flow")
    assert rows["code"].iloc[0] == "600000" and rows["date"].notna().all()
