import pandas as pd


def test_spot_snapshot_normalizes(monkeypatch):
    from aquant.data.sources import akshare_source as src
    raw = pd.DataFrame({
        "代码": ["600000", "1"], "名称": ["浦发", "平安"],
        "最新价": [10.1, 20.2], "涨跌幅": [1.2, -0.5],
        "换手率": [1.5, 2.0], "成交额": [1e8, 2e8],
    })
    monkeypatch.setattr(src.ak, "stock_zh_a_spot_em", lambda: raw)
    df = src.spot_snapshot()
    assert list(df.columns) == ["code", "name", "close", "pct_chg", "turnover", "amount"]
    assert df["code"].tolist() == ["600000", "000001"]  # 补零
    assert df.loc[df["code"] == "600000", "close"].iloc[0] == 10.1
