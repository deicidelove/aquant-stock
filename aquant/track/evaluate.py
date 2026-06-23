"""推荐台账评估（无状态，纯读）。

把 picks_log 的推荐快照 join daily_bar / index_daily 现算前向收益与超额，产出
live 记分卡。前向收益不入库——是 (entry_close, 后续行情) 的纯函数，每次现算，
永不陈旧。

口径：
- 前向收益 fwd_h = close_{t+h} / entry_close - 1（t+h 为 as_of 后第 h 个交易日）。
- 超额 exc_h   = fwd_h - 沪深300 同期收益。
- 交易日历以沪深300(index_daily) 为准：as_of 之后不足 h 个交易日 → pending（NaN，
  不参与统计，避免幸存偏差）；个股提前没行情（停牌/退市）→ 用最后可得价并打 flag。
"""
from __future__ import annotations

from bisect import bisect_right

import pandas as pd

from ..data import store

TABLE = "picks_log"
HORIZONS = (5, 20, 60)
BENCH = "sh000300"


def _calendar() -> tuple[list[str], dict]:
    """沪深300 交易日历 + 收盘价（作为前向收益的市场基准/计日尺）。"""
    if not store.has_table("index_daily"):
        return [], {}
    df = store.query("SELECT date, close FROM index_daily WHERE code = ? ORDER BY date", [BENCH])
    return df["date"].tolist(), dict(zip(df["date"], df["close"]))


def forward_returns(horizons=HORIZONS) -> pd.DataFrame:
    """逐推荐算各持有期前向收益与超额。返回台账明细 + fwd_h / exc_h 列。

    fwd_h 为 NaN 表示该档窗口未到期(pending)；delisted 列标记个股提前停牌/退市。
    """
    if not store.has_table(TABLE):
        return pd.DataFrame()
    ledger = store.query(f"SELECT * FROM {TABLE} ORDER BY as_of, rank")
    if ledger.empty:
        return ledger

    cal, bench_close = _calendar()
    # 个股收盘序列：code -> (有序日期列表, date->close)
    codes = ledger["code"].unique().tolist()
    bars = store.query(
        "SELECT code, date, close FROM daily_bar WHERE code IN ({}) ORDER BY code, date".format(
            ",".join("?" * len(codes))), codes)
    px: dict[str, tuple[list, dict]] = {}
    for code, g in bars.groupby("code", sort=False):
        px[code] = (g["date"].tolist(), dict(zip(g["date"], g["close"])))

    out = ledger.copy()
    for h in horizons:
        out[f"fwd_{h}"] = pd.NA
        out[f"exc_{h}"] = pd.NA
    out["delisted"] = False

    for i, r in ledger.iterrows():
        a, code, entry = r["as_of"], r["code"], r["entry_close"]
        cp = bisect_right(cal, a) - 1 if cal else -1          # as_of 在日历中的位置
        sdates, sclose = px.get(code, ([], {}))
        sp = bisect_right(sdates, a) - 1                        # as_of 在个股序列中的位置
        for h in horizons:
            # 市场是否已走满 h 个交易日（pending 判定以日历为准）
            market_ready = cp >= 0 and cp + h < len(cal)
            bench_fwd = None
            if market_ready:
                bench_fwd = bench_close[cal[cp + h]] / bench_close[cal[cp]] - 1
            # 个股前向价
            if sp >= 0 and sp + h < len(sdates):
                fwd = sclose[sdates[sp + h]] / entry - 1
            elif market_ready and sp >= 0:
                # 市场已到期但个股没行情 → 停牌/退市，用最后可得价
                fwd = sclose[sdates[-1]] / entry - 1
                out.at[i, "delisted"] = True
            else:
                fwd = None                                     # pending
            if fwd is not None:
                out.at[i, f"fwd_{h}"] = round(fwd, 4)
                if bench_fwd is not None:
                    out.at[i, f"exc_{h}"] = round(fwd - bench_fwd, 4)
    for h in horizons:
        out[f"fwd_{h}"] = pd.to_numeric(out[f"fwd_{h}"], errors="coerce")
        out[f"exc_{h}"] = pd.to_numeric(out[f"exc_{h}"], errors="coerce")
    return out


def scorecard(horizons=HORIZONS, min_names: int = 5) -> str:
    """live 记分卡（markdown）：Top-N 平均超额(外部有效性) + live Rank-IC(池内排序)。"""
    fr = forward_returns(horizons)
    if fr.empty:
        return "（picks_log 为空，先跑 `track-backfill` 或积累每日快照）"

    n_snap = fr["as_of"].nunique()
    lines = [
        "# 推荐跟踪记分卡",
        "",
        f"> 样本：{len(fr)} 条推荐 / {n_snap} 个快照日 "
        f"（{fr['as_of'].min()} ~ {fr['as_of'].max()}）。"
        f"实时 {int((fr['signal'] != 'reconstruct').sum())} 条 / "
        f"回放 {int((fr['signal'] == 'reconstruct').sum())} 条。",
        "",
        "## Top-N 平均超额（相对沪深300，外部有效性头号指标）",
        "",
        "| 持有期 | 已结算 | pending | 平均超额 | 正超额胜率 | 平均绝对收益 |",
        "|---|---|---|---|---|---|",
    ]
    for h in horizons:
        exc = fr[f"exc_{h}"].dropna()
        fwd = fr[f"fwd_{h}"].dropna()
        pend = int(fr[f"fwd_{h}"].isna().sum())
        if exc.empty:
            lines.append(f"| T+{h} | 0 | {pend} | — | — | — |")
            continue
        lines.append(
            f"| T+{h} | {len(exc)} | {pend} | {exc.mean()*100:+.2f}% | "
            f"{(exc > 0).mean()*100:.1f}% | {fwd.mean()*100:+.2f}% |")

    lines += [
        "",
        "## Live Rank-IC（score 与前向收益的截面 Spearman，对照 README 回测 IC）",
        "",
        "> 注：台账只存 Top-N，Rank-IC 仅衡量**已推荐集合内部**排序质量，非全市场多空。",
        "",
        "| 持有期 | 截面数 | 平均 Rank-IC | IR(IC均值/IC标准差) |",
        "|---|---|---|---|",
    ]
    for h in horizons:
        ics = []
        for _, g in fr.groupby("as_of"):
            sub = g[["score", f"fwd_{h}"]].dropna()
            if len(sub) >= min_names:
                ics.append(sub["score"].corr(sub[f"fwd_{h}"], method="spearman"))
        ics = pd.Series(ics).dropna()
        if ics.empty:
            lines.append(f"| T+{h} | 0 | — | — |")
            continue
        ir = ics.mean() / ics.std(ddof=0) if ics.std(ddof=0) else float("nan")
        lines.append(f"| T+{h} | {len(ics)} | {ics.mean():+.4f} | {ir:+.3f} |")

    delisted = int(fr["delisted"].sum())
    if delisted:
        lines += ["", f"> ⚠ 含 {delisted} 条停牌/退市标的（前向收益用最后可得价，"
                  "存幸存者偏差，实盘前需打折）。"]
    lines += ["", "> 仅供研究参考，不构成投资建议。"]
    return "\n".join(lines)
