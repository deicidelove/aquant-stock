"""大盘复盘 + 市场策略（自上而下）。

- breadth(): 市场宽度——涨跌家数、站上 MA20/MA60 比例、涨停近似。
- index_trend(): 沪深300/中证500 相对自身均线的位置与近期动量。
- regime(): 综合宽度+指数趋势 → 进攻 / 均衡 / 防守，给出仓位建议与理由。

全部基于本地 daily_bar + index_daily，确定性、无外部依赖。
"""
from __future__ import annotations

import pandas as pd

from .data import store


def breadth() -> dict:
    """最新交易日市场宽度（DuckDB 窗口一次算出每只的 MA 与位置）。"""
    if not store.has_table("daily_bar"):
        return {}
    # 取每只最新一行的 close 及其 MA20/MA60（窗口函数）
    df = store.query("""
        SELECT code, close, ma20, ma60, pct_chg FROM (
          SELECT code, date, close, pct_chg,
                 avg(close) OVER (PARTITION BY code ORDER BY date ROWS 19 PRECEDING) ma20,
                 avg(close) OVER (PARTITION BY code ORDER BY date ROWS 59 PRECEDING) ma60,
                 row_number() OVER (PARTITION BY code ORDER BY date DESC) rn
          FROM daily_bar) t
        WHERE rn = 1
    """)
    if df.empty:
        return {}
    n = len(df)
    up = int((df["pct_chg"] > 0).sum())
    down = int((df["pct_chg"] < 0).sum())
    limit_up = int((df["pct_chg"] >= 9.8).sum())   # 近似涨停（不含20cm板）
    above20 = round((df["close"] > df["ma20"]).mean() * 100, 1)
    above60 = round((df["close"] > df["ma60"]).mean() * 100, 1)
    return {"total": n, "up": up, "down": down, "limit_up": limit_up,
            "up_ratio": round(up / n * 100, 1),
            "above_ma20_pct": above20, "above_ma60_pct": above60}


def index_trend(code: str = "sh000300") -> dict:
    """指数相对均线位置 + 近期动量。"""
    if not store.has_table("index_daily"):
        return {}
    df = store.query("SELECT date, close FROM index_daily WHERE code=? ORDER BY date", [code])
    if len(df) < 60:
        return {}
    c = df["close"]
    ma20, ma60 = c.rolling(20).mean().iloc[-1], c.rolling(60).mean().iloc[-1]
    last = c.iloc[-1]
    return {"code": code, "close": round(float(last), 2),
            "above_ma20": bool(last > ma20), "above_ma60": bool(last > ma60),
            "ret_20d": round((last / c.iloc[-21] - 1) * 100, 2) if len(c) > 21 else None,
            "ret_60d": round((last / c.iloc[-61] - 1) * 100, 2) if len(c) > 61 else None}


def regime() -> dict:
    """综合判断市场状态：进攻 / 均衡 / 防守。"""
    b = breadth()
    idx = index_trend("sh000300")
    if not b or not idx:
        return {}
    # 打分：宽度 + 指数趋势
    score = 0
    if b["above_ma20_pct"] >= 60: score += 2
    elif b["above_ma20_pct"] >= 40: score += 1
    if b["above_ma60_pct"] >= 50: score += 1
    if b["up_ratio"] >= 55: score += 1
    if idx["above_ma20"]: score += 1
    if idx["above_ma60"]: score += 1
    if (idx.get("ret_20d") or 0) > 0: score += 1

    if score >= 5:
        state, pos, note = "进攻", "7~9成", "宽度健康、指数多头，可积极持仓"
    elif score >= 3:
        state, pos, note = "均衡", "4~6成", "多空交织，控制仓位、精选个股"
    else:
        state, pos, note = "防守", "1~3成", "宽度走弱、指数空头，降仓避险为主"
    return {"state": state, "score": score, "suggested_position": pos, "note": note,
            "breadth": b, "index": idx}


def review_markdown() -> str:
    r = regime()
    if not r:
        return "（数据不足：需 daily_bar 与 index_daily）"
    b, idx = r["breadth"], r["index"]
    icon = {"进攻": "🔴", "均衡": "🟡", "防守": "🟢"}.get(r["state"], "")
    return "\n".join([
        f"# 大盘复盘（{store.query('SELECT max(date) d FROM daily_bar')['d'].iloc[0]}）", "",
        f"## {icon} 市场状态：**{r['state']}**（{r['score']}/7）　建议仓位 {r['suggested_position']}", "",
        f"> {r['note']}", "",
        f"**市场宽度**：{b['total']} 只中 涨 {b['up']} / 跌 {b['down']}（涨占比 {b['up_ratio']}%），"
        f"近似涨停 {b['limit_up']}；站上 MA20 **{b['above_ma20_pct']}%**、站上 MA60 **{b['above_ma60_pct']}%**", "",
        f"**沪深300**：{idx['close']}　{'站上' if idx['above_ma20'] else '跌破'} MA20、"
        f"{'站上' if idx['above_ma60'] else '跌破'} MA60；近20日 {idx.get('ret_20d')}%、近60日 {idx.get('ret_60d')}%",
    ])
