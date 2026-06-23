"""全局配置与路径。本地个人工具，约定优于配置。"""
from __future__ import annotations

import os
from pathlib import Path

# 项目根目录（aquant 的上一级）
ROOT = Path(__file__).resolve().parent.parent

# 本地数据仓库：DuckDB 主库 + parquet 落地（均在 .gitignore 中）
DATA_DIR = Path(os.getenv("AQUANT_DATA_DIR", ROOT / "data_store"))
DB_PATH = DATA_DIR / "market.duckdb"
PARQUET_DIR = DATA_DIR / "parquet"

# 复权方式：qfq 前复权（量化研究默认），可选 hfq/none
ADJUST = os.getenv("AQUANT_ADJUST", "qfq")

# A 股最早可取数据起点（akshare 日线足够早即可）
HISTORY_START = os.getenv("AQUANT_HISTORY_START", "20180101")

# 网络重试
RETRY_ATTEMPTS = 4
RETRY_WAIT_SECONDS = 2

for _d in (DATA_DIR, PARQUET_DIR):
    _d.mkdir(parents=True, exist_ok=True)
