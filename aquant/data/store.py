"""DuckDB 本地行情仓库。

- 单文件 DuckDB，列式、本地、SQL 直查，批量读取快。
- 每表声明主键，写入用 INSERT OR REPLACE 实现幂等 upsert（增量更新可重复跑）。
- 表结构按需建立（按 DataFrame 列推断类型），新增数据维度无需手写 DDL。
"""
from __future__ import annotations

from contextlib import contextmanager

import duckdb
import pandas as pd

from .. import config

# 表 -> 主键列。决定 upsert 的去重粒度。
TABLE_KEYS: dict[str, list[str]] = {
    "stock_basic": ["code"],
    "daily_bar": ["code", "date"],
    "fund_flow": ["code", "date"],
    "sector_daily": ["sector", "date"],
    "sector_member": ["sector", "code"],
    "lhb_detail": ["code", "date", "reason"],
    "lhb_seat": ["code", "date", "side", "seat"],
    "index_daily": ["code", "date"],
    "fundamental": ["code", "date"],
    "picks_log": ["as_of", "code"],
    "quote_snapshot": ["code", "ts"],
    "sector_snapshot": ["sector", "ts"],
    "sector_fund_flow": ["sector", "date"],
    "factor_score": ["code", "as_of"],
    "news_cache": ["code", "as_of"],
    "market_news": ["time", "title"],
    "limit_pool": ["code", "date"],
    "north_flow": ["date", "market"],
    "research_report": ["code", "as_of"],
    "fund_context_cache": ["code", "as_of"],
    "trades": ["tid"],
    "quant_jobs": ["job_id"],
    "watchlist": ["code"],
}


@contextmanager
def connect():
    con = duckdb.connect(str(config.DB_PATH))
    try:
        yield con
    finally:
        con.close()


def _ddl_type(dtype) -> str:
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    return "VARCHAR"


def _ensure_table(con, table: str, df: pd.DataFrame) -> None:
    cols = [f'"{c}" {_ddl_type(df[c].dtype)}' for c in df.columns]
    keys = TABLE_KEYS.get(table)
    if keys and all(k in df.columns for k in keys):
        quoted = ", ".join(f'"{k}"' for k in keys)
        cols.append(f"PRIMARY KEY ({quoted})")
    con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(cols)})')


def save(table: str, df: pd.DataFrame) -> int:
    """幂等写入（按主键 INSERT OR REPLACE），返回写入行数。"""
    if df is None or df.empty:
        return 0
    df = df.reset_index(drop=True)
    with connect() as con:
        _ensure_table(con, table, df)
        target_cols = [r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ? ORDER BY ordinal_position", [table]).fetchall()]
        common = [c for c in target_cols if c in df.columns]
        col_list = ", ".join(f'"{c}"' for c in common)
        con.register("_incoming", df)
        con.execute(f'INSERT OR REPLACE INTO "{table}" ({col_list}) '
                    f'SELECT {col_list} FROM _incoming')
        con.unregister("_incoming")
    return len(df)


def query(sql: str, params: list | None = None) -> pd.DataFrame:
    with connect() as con:
        return con.execute(sql, params or []).df()


def has_table(table: str) -> bool:
    with connect() as con:
        r = con.execute("SELECT count(*) FROM information_schema.tables "
                        "WHERE table_name = ?", [table]).fetchone()
        return bool(r and r[0])


def max_date(table: str, code: str | None = None) -> str | None:
    """已有最大日期，用于增量更新断点续传。"""
    if not has_table(table):
        return None
    with connect() as con:
        if code is not None:
            r = con.execute(f'SELECT max("date") FROM "{table}" WHERE code = ?', [code]).fetchone()
        else:
            r = con.execute(f'SELECT max("date") FROM "{table}"').fetchone()
        return r[0] if r and r[0] is not None else None


def load_daily(code: str) -> pd.DataFrame:
    """读单只股票全部日线，按日期升序。"""
    return query('SELECT * FROM daily_bar WHERE code = ? ORDER BY date', [code])


def summary() -> pd.DataFrame:
    """daily_bar 概览：每只股票行数与起止日期。"""
    if not has_table("daily_bar"):
        return pd.DataFrame(columns=["code", "rows", "start", "end"])
    return query('SELECT code, COUNT(*) AS rows, MIN(date) AS start, MAX(date) AS end '
                 'FROM daily_bar GROUP BY code ORDER BY code')
