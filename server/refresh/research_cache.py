"""研投缓存预取：盘后给驾驶舱可见集合（高分+建仓名单）抓新闻/财务筹码落库。

只在后台运行；抓取失败按 code 降级（不影响其他）。读取在 aquant.data.research_cache。
"""
from __future__ import annotations

from aquant.data import store
from aquant.data import research_cache as rc
from aquant.data.sources.news import stock_news
from aquant.data.sources import fundamental as fund
from aquant import research
from server.refresh import scores


def prefetch_universe(top: int = 120) -> list[str]:
    """驾驶舱可见集合：高分 Top-N 的 code ∪ 每日建仓名单的 code。"""
    codes: set[str] = set()
    s = scores.read_top_scores(top=top)
    if not s.empty:
        codes |= set(s["code"])
    p = research.daily_picks()
    if not p.empty:
        codes |= set(p["code"])
    return sorted(codes)


def prefetch_research(codes=None, news_fetch=None, ctx_fetch=None) -> int:
    """对集合内每只抓新闻+上下文写缓存，返回成功缓存的 code 数。"""
    codes = codes if codes is not None else prefetch_universe()
    news_fetch = news_fetch or (lambda c: stock_news(c, limit=8))
    ctx_fetch = ctx_fetch or (lambda c: fund.context(c))
    as_of = store.max_date("daily_bar")
    if as_of is None or not codes:
        return 0
    done = 0
    for code in codes:
        try:
            rc.save_news(code, as_of, news_fetch(code) or [])
            rc.save_context(code, as_of, ctx_fetch(code) or {})
            done += 1
        except Exception:  # noqa: BLE001 单只失败降级，不影响其他
            continue
    return done
