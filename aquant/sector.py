"""板块中观：主线判断 + 轮动信号（延续/新晋/退潮）。

- main_lines(): 当日主线候选——按涨幅与赚钱效应(上涨家数占比)排序。
- rotation(): 今日 Top 板块 vs 上一交易日快照 → persisted/emerged/faded。
  需 sector_daily 累积 ≥2 个交易日快照；只有 1 日时返回"首次快照"。
"""
from __future__ import annotations

import pandas as pd

from .data import store

FADE_RANK = 10  # 跌出前10视为退潮


def _snapshot(date: str) -> pd.DataFrame:
    df = store.query("SELECT * FROM sector_daily WHERE date = ?", [date])
    if "up_count" in df.columns and "down_count" in df.columns:
        tot = (df["up_count"].fillna(0) + df["down_count"].fillna(0)).replace(0, 1)
        df["win_ratio"] = (df["up_count"].fillna(0) / tot * 100).round(1)
    return df


def main_lines(top: int = 8) -> pd.DataFrame:
    """当日主线候选：涨幅 + 赚钱效应。"""
    if not store.has_table("sector_daily"):
        return pd.DataFrame()
    latest = store.query("SELECT max(date) d FROM sector_daily")["d"].iloc[0]
    df = _snapshot(latest).sort_values("pct_chg", ascending=False)
    cols = [c for c in ["sector", "pct_chg", "win_ratio", "turnover", "leader"] if c in df.columns]
    return df[cols].head(top).reset_index(drop=True)


def rotation(top: int = 10) -> dict:
    """轮动信号：对比最近两个交易日的 Top 板块。"""
    if not store.has_table("sector_daily"):
        return {}
    dates = store.query("SELECT DISTINCT date FROM sector_daily ORDER BY date DESC LIMIT 2")["date"].tolist()
    if len(dates) < 2:
        return {"status": "首次快照，无对比（需累积≥2个交易日）",
                "today": dates[0] if dates else None}
    today, prev = dates[0], dates[1]
    t = _snapshot(today).sort_values("pct_chg", ascending=False).reset_index(drop=True)
    p = _snapshot(prev).sort_values("pct_chg", ascending=False).reset_index(drop=True)
    t_top = t["sector"].head(top).tolist()
    p_top = p["sector"].head(top).tolist()
    p_rank = {s: i for i, s in enumerate(p["sector"].tolist())}
    persisted = [s for s in t_top if s in p_top]
    emerged = [s for s in t_top if s not in p_top]
    faded = [s for s in p_top if p_rank.get(s, 999) < FADE_RANK
             and (s not in set(t["sector"].head(FADE_RANK)))]
    return {"today": today, "prev": prev, "persisted": persisted,
            "emerged": emerged, "faded": faded}


def review_markdown(top: int = 8) -> str:
    ml = main_lines(top)
    if ml.empty:
        return "（无板块数据：先 `python -m aquant.cli sectors`）"
    rot = rotation()
    lines = [f"## 📈 板块主线（{store.query('SELECT max(date) d FROM sector_daily')['d'].iloc[0]}）", "",
             "| 板块 | 涨跌幅 | 赚钱效应 | 领涨 |", "|---|---|---|---|"]
    for r in ml.itertuples(index=False):
        lines.append(f"| {r.sector} | {getattr(r,'pct_chg','')}% | "
                     f"{getattr(r,'win_ratio','-')}% | {getattr(r,'leader','')} |")
    lines.append("")
    if rot.get("persisted") is not None:
        lines += ["**轮动信号**", "",
                  f"- 🔵 延续：{', '.join(rot['persisted']) or '—'}",
                  f"- 🟢 新晋：{', '.join(rot['emerged']) or '—'}",
                  f"- 🔴 退潮：{', '.join(rot['faded']) or '—'}"]
    else:
        lines.append(f"*{rot.get('status','')}*")
    return "\n".join(lines)
