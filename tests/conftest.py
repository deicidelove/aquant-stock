import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# 必须在 import 任何 aquant 模块之前设置数据目录
_TMP = tempfile.mkdtemp(prefix="aquant_test_")
os.environ["AQUANT_DATA_DIR"] = _TMP


@pytest.fixture()
def seed_db():
    """向临时 DuckDB 写入最小行情数据：2 只股票、各 80 个交易日。"""
    from aquant.data import store
    dates = pd.bdate_range("2026-01-01", periods=80).strftime("%Y-%m-%d").tolist()
    rows = []
    for code, base in (("600000", 10.0), ("000001", 20.0)):
        for i, d in enumerate(dates):
            px = base + i * 0.05
            rows.append({"code": code, "date": d, "open": px, "high": px * 1.02,
                         "low": px * 0.98, "close": px, "volume": 1e6 + i,
                         "amount": px * 1e7, "turnover": 1.5, "pct_chg": 0.5})
    store.save("daily_bar", pd.DataFrame(rows))
    store.save("stock_basic", pd.DataFrame(
        [{"code": "600000", "name": "浦发银行", "market": "sh"},
         {"code": "000001", "name": "平安银行", "market": "sz"}]))
    return store


@pytest.fixture()
def client(seed_db):
    from fastapi.testclient import TestClient
    from server.app import create_app
    return TestClient(create_app(start_scheduler=False))
