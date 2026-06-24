"""研投缓存表（新闻/财务筹码上下文）的纯 DuckDB 读写。

数据由 server.refresh.research_cache 后台预取写入；此模块只做落库与读取，
不触网，供 aquant.research 离线读取（避免 aquant→server 反向依赖）。
按 (code, as_of) 存，各存一行 JSON blob。
"""
from __future__ import annotations

import json

import pandas as pd

from . import store


def save_news(code: str, as_of: str, items: list[dict]) -> int:
    df = pd.DataFrame([{"code": code, "as_of": as_of,
                        "news_json": json.dumps(items, ensure_ascii=False)}])
    return store.save("news_cache", df)


def save_context(code: str, as_of: str, ctx: dict) -> int:
    df = pd.DataFrame([{"code": code, "as_of": as_of,
                        "ctx_json": json.dumps(ctx, ensure_ascii=False)}])
    return store.save("fund_context_cache", df)


def read_news(code: str) -> list[dict]:
    if not store.has_table("news_cache"):
        return []
    df = store.query("SELECT news_json FROM news_cache WHERE code=? "
                     "ORDER BY as_of DESC LIMIT 1", [code])
    return json.loads(df["news_json"].iloc[0]) if not df.empty else []


def read_context(code: str) -> dict:
    if not store.has_table("fund_context_cache"):
        return {}
    df = store.query("SELECT ctx_json FROM fund_context_cache WHERE code=? "
                     "ORDER BY as_of DESC LIMIT 1", [code])
    return json.loads(df["ctx_json"].iloc[0]) if not df.empty else {}
