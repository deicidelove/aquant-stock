"""龙虎榜刷新任务：抓上榜列表 + 逐只席位 → 落 DuckDB。后台运行（非请求路径）。"""
from __future__ import annotations

from datetime import date, timedelta

from aquant.data import store
from aquant.data.sources import akshare_source as src
from aquant.lhb import classify_seat


def refresh_lhb(days: int = 1) -> int:
    """抓最近 days 个自然日的上榜列表存 lhb_detail；对最新上榜日每只个股抓买/卖席位存 lhb_seat。

    返回写入行数（detail + seat）。
    """
    end = date.today()
    start = end - timedelta(days=max(days, 1) + 6)  # 多给几天余量覆盖节假日
    detail = src.lhb_detail(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    if detail is None or detail.empty:
        return 0
    detail = detail.copy()
    if "reason" in detail.columns:  # reason 是主键，真实数据可能为空
        detail["reason"] = detail["reason"].fillna("").astype(str)
    written = store.save("lhb_detail", detail)

    latest = str(detail["date"].max())
    codes = detail.loc[detail["date"] == latest, "code"].astype(str).tolist()
    for code in codes:
        for side, flag in (("buy", "买入"), ("sell", "卖出")):
            try:
                seats = src.lhb_seats(code, latest, flag)
            except Exception:
                continue
            if seats is None or seats.empty:
                continue
            seats = seats.copy()
            seats["code"] = code
            seats["date"] = latest
            seats["side"] = side
            types = seats["seat"].map(classify_seat)
            seats["seat_type"] = [t[0] for t in types]
            seats["hotmoney_name"] = [t[1] for t in types]
            written += store.save("lhb_seat", seats)
    return written
