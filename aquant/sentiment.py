"""新闻情绪（关键词法，离线、可解释）。

- score_text：单条文本 → 利好(+1)/利空(-1)/中性(0)。
- aggregate：多条 → 0-100 情绪指数 + 分档标签。
- market_news_sentiment：读 market_news 表聚合（只读 DuckDB）。
"""
from __future__ import annotations

from aquant.data import store

# 利好 / 利空 关键词。覆盖个股 + 宏观。可后续扩充。
POS = (
    "降准", "降息", "宽松", "利好", "政策支持", "减税", "补贴", "外资流入", "北向净买",
    "中标", "回购", "增持", "预增", "扭亏", "新高", "合作", "获批", "订单", "分红",
    "重组", "涨停", "突破", "创新高", "超预期", "提振", "复苏", "反弹",
)
NEG = (
    "加息", "收紧", "利空", "监管", "违约", "暴雷", "风险", "外资流出", "北向净卖",
    "减持", "预亏", "亏损", "立案", "处罚", "问询", "退市", "质押", "诉讼",
    "下滑", "商誉", "跌停", "暴跌", "低于预期", "承压", "衰退", "利空出尽",
)


def score_text(text: str) -> int:
    t = text or ""
    if any(k in t for k in POS):
        return 1
    if any(k in t for k in NEG):
        return -1
    return 0


def _label(score: int) -> str:
    if score >= 75:
        return "极度乐观"
    if score >= 60:
        return "乐观"
    if score > 40:
        return "中性"
    if score > 25:
        return "谨慎"
    return "悲观"


def aggregate(items: list[dict]) -> dict:
    pos = sum(1 for x in items if x.get("sent") == 1)
    neg = sum(1 for x in items if x.get("sent") == -1)
    neutral = sum(1 for x in items if x.get("sent") == 0)
    denom = pos + neg
    score = 50 if denom == 0 else round(50 + 50 * (pos - neg) / denom)
    score = max(0, min(100, score))
    return {"score": score, "label": _label(score),
            "pos": pos, "neg": neg, "neutral": neutral}


def market_news_sentiment(limit: int = 30) -> dict:
    empty = {"score": 50, "label": _label(50), "pos": 0, "neg": 0, "neutral": 0, "items": []}
    if not store.has_table("market_news"):
        return empty
    df = store.query(
        "SELECT time,title,summary,url,sent FROM market_news ORDER BY time DESC LIMIT ?",
        [limit])
    if df.empty:
        return empty
    items = [{"time": r["time"], "title": r["title"], "summary": r["summary"],
              "url": r["url"], "sent": int(r["sent"])} for _, r in df.iterrows()]
    agg = aggregate(items)
    agg["items"] = items
    return agg
