"""个股资讯（东财新闻，免 key/免 docker）。"""
from __future__ import annotations

import akshare as ak
import pandas as pd

from .akshare_source import _robust


@_robust
def stock_news(code: str, limit: int = 8) -> list[dict]:
    """个股近期新闻：标题/时间/来源。"""
    df = ak.stock_news_em(symbol=code)
    if df is None or df.empty:
        return []
    df = df.rename(columns={"新闻标题": "title", "发布时间": "time", "文章来源": "source"})
    keep = [c for c in ("title", "time", "source") if c in df.columns]
    return df[keep].head(limit).to_dict("records")
