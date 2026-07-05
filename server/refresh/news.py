"""市场消息面刷新任务：抓全市场财经快讯 + 情绪打分 → 落 DuckDB。后台运行。"""
from __future__ import annotations

import pandas as pd

from aquant.data import store
from aquant.data.sources import news as src
from aquant.sentiment import score_text


def refresh_market_news(limit: int = 50) -> int:
    """抓快讯，逐条打情绪分，upsert 到 market_news。返回写入行数。"""
    items = src.market_news(limit=limit)
    if not items:
        return 0
    df = pd.DataFrame(items)
    for col in ("title", "summary", "time", "url"):
        if col not in df.columns:
            df[col] = ""
    df["title"] = df["title"].fillna("").astype(str)
    df["summary"] = df["summary"].fillna("").astype(str)
    df["time"] = df["time"].fillna("").astype(str)
    df["url"] = df["url"].fillna("").astype(str)
    df["sent"] = (df["title"] + " " + df["summary"]).map(score_text)
    return store.save("market_news", df[["time", "title", "summary", "url", "sent"]])
