"""涨停梯队 / 北向 域层（只读 DuckDB，请求路径不发网络）。

A股情绪核心：连板高度分布、封板率、炸板率、涨停家数、行业分布。
"""
from __future__ import annotations

from aquant.data import store


def _latest(table: str) -> str | None:
    if not store.has_table(table):
        return None
    df = store.query(f"SELECT MAX(date) AS d FROM {table}")
    return None if df.empty or df["d"].iloc[0] is None else str(df["d"].iloc[0])


def limit_ladder(date: str | None = None) -> dict:
    """涨停梯队 + 情绪指标。"""
    empty = {"date": None, "limit_up_count": 0, "seal_rate": None,
             "break_rate": None, "max_boards": 0, "ladder": [], "by_industry": []}
    date = date or _latest("limit_pool")
    if date is None:
        return empty
    df = store.query(
        "SELECT code,name,boards,break_times,seal_fund,industry FROM limit_pool "
        "WHERE date=? ORDER BY boards DESC, seal_fund DESC", [date])
    if df.empty:
        return {**empty, "date": date}

    n = len(df)
    broke = int((df["break_times"].fillna(0) > 0).sum())
    ladder = []
    for b in sorted(df["boards"].dropna().unique(), reverse=True):
        grp = df[df["boards"] == b]
        ladder.append({"boards": int(b), "count": int(len(grp)),
                       "names": grp["name"].head(8).tolist()})
    by_ind = (df.groupby("industry").size().sort_values(ascending=False)
              .head(8).reset_index(name="count"))
    by_industry = [{"industry": r["industry"], "count": int(r["count"])}
                   for _, r in by_ind.iterrows()]
    return {
        "date": date,
        "limit_up_count": n,
        "seal_rate": round((n - broke) / n, 3) if n else None,
        "break_rate": round(broke / n, 3) if n else None,
        "max_boards": int(df["boards"].max()),
        "ladder": ladder,
        "by_industry": by_industry,
    }


def north_flow(date: str | None = None) -> dict:
    """北向资金各通道净流入。"""
    date = date or _latest("north_flow")
    if date is None:
        return {"date": None, "rows": []}
    df = store.query(
        "SELECT market,net FROM north_flow WHERE date=? ORDER BY net DESC", [date])
    rows = [{"market": r["market"], "net": _f(r["net"])} for _, r in df.iterrows()]
    return {"date": date, "rows": rows}


def _f(v):
    try:
        import pandas as pd
        return None if v is None or pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return None
