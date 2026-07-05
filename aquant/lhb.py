"""龙虎榜域层（只读 DuckDB，请求路径不发网络）。

- classify_seat：把营业部名称归类成 机构 / 北向 / 游资 / 普通。
- lhb_today / lhb_stock：读 lhb_detail / lhb_seat 聚合。
"""
from __future__ import annotations

from aquant.data import store

# 知名游资营业部关键字 → 别名。可后续扩充。
# 关键字取营业部名中稳定可辨的片段，命中即打标。
HOTMONEY: dict[str, str] = {
    "绍兴": "章盟主",
    "泺源大街": "赵老哥",
    "佛山": "佛山无影脚",
    "上海溧阳路": "养家(炒股养家)",
    "无锡清扬路": "苏南帮",
    "深圳益田路荣超商务中心": "深圳帮",
    "拉萨团结路": "量化/东财拉萨",
    "拉萨东环路": "量化/东财拉萨",
}


def classify_seat(name: str) -> tuple[str, str | None]:
    """(seat_type, hotmoney_name|None)。seat_type ∈ inst/north/hotmoney/normal。"""
    n = name or ""
    if "机构专用" in n:
        return "inst", None
    if "股通专用" in n or "沪股通" in n or "深股通" in n:
        return "north", None
    for kw, alias in HOTMONEY.items():
        if kw in n:
            return "hotmoney", alias
    return "normal", None


def _latest_date() -> str | None:
    if not store.has_table("lhb_detail"):
        return None
    df = store.query("SELECT MAX(date) AS d FROM lhb_detail")
    return None if df.empty or df["d"].iloc[0] is None else str(df["d"].iloc[0])


def _tags_for(code: str, date: str) -> list[str]:
    """由该股席位聚合推断标签：机构 / 北向 / 游资别名。"""
    if not store.has_table("lhb_seat"):
        return []
    df = store.query(
        "SELECT DISTINCT seat_type, hotmoney_name FROM lhb_seat WHERE code=? AND date=?",
        [code, date],
    )
    tags: list[str] = []
    types = set(df["seat_type"].tolist())
    if "inst" in types:
        tags.append("机构")
    if "north" in types:
        tags.append("北向")
    for nm in df["hotmoney_name"].dropna().unique().tolist():
        if nm:
            tags.append(str(nm))
    return tags


def lhb_today(limit: int = 50) -> dict:
    """最近一个上榜交易日的个股列表，按净买额降序。"""
    date = _latest_date()
    if date is None:
        return {"date": None, "rows": []}
    df = store.query(
        "SELECT code,name,pct_chg,lhb_net_buy,lhb_amount,reason FROM lhb_detail "
        "WHERE date=? ORDER BY lhb_net_buy DESC LIMIT ?",
        [date, limit],
    )
    rows = []
    for _, x in df.iterrows():
        rows.append({
            "code": x["code"], "name": x["name"],
            "pct_chg": _f(x["pct_chg"]), "lhb_net_buy": _f(x["lhb_net_buy"]),
            "lhb_amount": _f(x["lhb_amount"]), "reason": x["reason"] or "",
            "tags": _tags_for(x["code"], date),
        })
    return {"date": date, "rows": rows}


def lhb_stock(code: str, date: str | None = None) -> dict:
    """个股席位穿透。date 缺省取该股最近上榜日。"""
    empty = {"code": code, "name": None, "date": None, "reason": None, "buy": [], "sell": []}
    if not store.has_table("lhb_detail"):
        return empty
    if date is None:
        d = store.query("SELECT MAX(date) AS d FROM lhb_detail WHERE code=?", [code])
        if d.empty or d["d"].iloc[0] is None:
            return empty
        date = str(d["d"].iloc[0])
    head = store.query(
        "SELECT name,reason FROM lhb_detail WHERE code=? AND date=? LIMIT 1", [code, date])
    name = head["name"].iloc[0] if not head.empty else None
    reason = head["reason"].iloc[0] if not head.empty else None
    seats = {"buy": [], "sell": []}
    if store.has_table("lhb_seat"):
        sd = store.query(
            "SELECT side,rank,seat,buy,sell,net,seat_type,hotmoney_name FROM lhb_seat "
            "WHERE code=? AND date=? ORDER BY side, rank", [code, date])
        for _, x in sd.iterrows():
            item = {
                "rank": int(x["rank"]), "seat": x["seat"],
                "buy": _f(x["buy"]), "sell": _f(x["sell"]), "net": _f(x["net"]),
                "seat_type": x["seat_type"],
                "hotmoney_name": x["hotmoney_name"] if x["hotmoney_name"] else None,
            }
            seats.get(x["side"], []).append(item)
    return {"code": code, "name": name, "date": date, "reason": reason,
            "buy": seats["buy"], "sell": seats["sell"]}


def _f(v):
    try:
        import pandas as pd
        if v is None or pd.isna(v):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None
