"""每日决策流水线：把数据/因子/选股/信号串成可执行结论。

输出回答两个问题：
  1) 选什么股 —— 多因子打分 Top-N 候选池；
  2) 什么时候买卖 —— 每只候选的最新择时动作 + 关键价位（支撑/压力/止损）。

用法：
    from aquant.research import daily_picks, to_markdown
    picks = daily_picks(top=20, signal="ma_cross")
    print(to_markdown(picks))
或 CLI：python -m aquant.cli pick --top 20 --signal ma_cross
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import store
from .select import scorer
from .signal import timing

MIN_HISTORY = 60  # 计算因子/信号所需最少交易日

# 板块标签（按代码前缀）。北交所含 8xx/4xx/920 段。
BOARDS = ("主板", "创业", "科创", "北交")


def board_of(code: str) -> str:
    """按代码前缀判板块。"""
    if code[:3] in ("688", "689"):
        return "科创"
    if code[:3] in ("300", "301"):
        return "创业"
    if code[:1] in ("4", "8") or code[:3] == "920":
        return "北交"
    return "主板"


def universe(min_history: int = MIN_HISTORY, exclude_st: bool = True,
             min_amount: float = 5e7, drop_boards=None) -> list[str]:
    """可投资股票域。默认剔除三类不可投/会污染因子的标的：

    - 历史不足（次新股，因子算不准、上市初期高波动）；
    - ST/*ST（退市风险；且 5% 涨跌停限制使其波动人为偏低，会骗过低波因子）；
    - 流动性不足（近 60 日日均成交额 < min_amount，默认 5000 万，难成交）。

    drop_boards: 额外剔除的板块集合（如 {"科创","创业"}），可选；默认全域不剔，
    与 README 验证过的清洁全域口径一致。
    """
    if not store.has_table("daily_bar"):
        return []
    codes = set(store.query(
        "SELECT code FROM daily_bar GROUP BY code HAVING COUNT(*) >= ?",
        [min_history])["code"])

    if drop_boards:
        drop = set(drop_boards)
        codes = {c for c in codes if board_of(c) not in drop}

    if exclude_st and store.has_table("stock_basic"):
        names = store.query("SELECT code, name FROM stock_basic")
        # ST/*ST（退市风险、涨跌停受限）+ 已退市/退 + 新股 N/C 标记，统统剔除
        bad = names["name"].str.contains("ST|退|^[NC] ?", case=False, na=False, regex=True)
        codes -= set(names[bad]["code"])

    if min_amount:
        liq = store.query(
            "SELECT code, avg(amount) a FROM ("
            "  SELECT code, amount, row_number() OVER "
            "    (PARTITION BY code ORDER BY date DESC) rn FROM daily_bar) t "
            "WHERE rn <= 60 GROUP BY code")
        codes &= set(liq[liq["a"] >= min_amount]["code"])

    return sorted(codes)


def _levels(df: pd.DataFrame) -> dict:
    """单只股票的关键价位。"""
    c = df["close"]
    last = c.iloc[-1]
    ma20 = c.rolling(20).mean().iloc[-1]
    ma60 = c.rolling(60).mean().iloc[-1]
    support = df["low"].rolling(20).min().iloc[-1]      # 20日最低=近端支撑
    resistance = df["high"].rolling(20).max().iloc[-1]  # 20日最高=近端压力
    # 止损：支撑与“收盘-2倍ATR近似(20日波动)”取较高者，避免止损过松
    atr_like = (df["high"] - df["low"]).rolling(20).mean().iloc[-1]
    stop = max(support, last - 2 * atr_like)
    return {
        "close": round(float(last), 2),
        "ma20": round(float(ma20), 2),
        "ma60": round(float(ma60), 2),
        "support": round(float(support), 2),
        "resistance": round(float(resistance), 2),
        "stop": round(float(stop), 2),
        "above_ma60": bool(last > ma60),
    }


def daily_picks(top: int = 20, signal: str = "ma_cross",
                as_of: str | None = None,
                weights: dict | None = None,
                require_uptrend: bool = False,
                drop_boards=None, min_amount: float = 5e7,
                only_actions: set[str] | None = None) -> pd.DataFrame:
    """选股 + 择时一体化。

    默认 require_uptrend=False，与验证过的季度低波/反转策略一致（该策略本就买
    被打下来的低波标的，不应叠加“价在 MA60 之上”的上涨过滤，否则二者冲突、选不出票）。
    若改用动量风格权重，可显式置 require_uptrend=True。

    drop_boards: 可选剔除板块（如 {"科创","创业"}）；缩小股票域同时显著提速打分。

    only_actions: 若给定（如 {"买入"}），只保留择时动作在此集合内的标的。因为“买入”
        是信号当日翻转才触发、数量稀少，此时会自动放大候选扫描池，尽量凑满 top 只；
        当日满足者不足 top 则返回较少（甚至空）。默认 None=不按动作过滤（旧行为）。
    """
    codes = universe(min_amount=min_amount, drop_boards=drop_boards)
    if not codes:
        return pd.DataFrame()

    # 只筛特定动作（如买入）时，当日触发者稀少，需放大候选池逐只扫到足够或耗尽。
    pool = top * 3 if only_actions is None else max(top * 100, 300)
    # 实时（无 as_of）走快速内存打分；指定历史日期才用逐只的慢速路径。
    if as_of:
        ranked = scorer.score(codes, weights=weights, as_of=as_of, top=pool)
    else:
        ranked = scorer.score_fast(codes=codes, weights=weights, top=pool)
    if ranked.empty:
        return pd.DataFrame()

    rows = []
    for _, r in ranked.iterrows():
        code = r["code"]
        df = store.load_daily(code)
        if as_of:
            df = df[df["date"] <= as_of]
        if len(df) < MIN_HISTORY:
            continue
        lv = _levels(df)
        if require_uptrend and not lv["above_ma60"]:
            continue
        act = timing.latest_action(df, signal)
        if only_actions is not None and act["action"] not in only_actions:
            continue
        rows.append({
            "code": code,
            "name": r.get("name", ""),
            "score": round(float(r["score"]), 3),
            "action": act["action"],
            **{k: lv[k] for k in ("close", "ma20", "ma60", "support", "resistance", "stop")},
            "signal_date": act["date"],
        })
        if len(rows) >= top:
            break
    return pd.DataFrame(rows)


def stock_report(code: str, market_scores: pd.DataFrame | None = None, offline: bool = False) -> dict:
    """单只股票研投报告数据：区间表现 + 因子明细 + 择时 + 关键价位 + 资金流。

    market_scores: 可选的全市场 (code,score) 表，用于算综合分与排名；不传则现算。
    注意：暂无 PE/PB 等基本面数据（未入库），报告聚焦价量/因子/资金面。
    """
    from .select import scorer
    from .factors import registry, technical  # noqa: F401
    df = store.load_daily(code)
    if df.empty or len(df) < MIN_HISTORY:
        return {}
    c = df["close"]
    name = ""
    if store.has_table("stock_basic"):
        r = store.query("SELECT name FROM stock_basic WHERE code = ?", [code])
        name = r["name"].iloc[0] if not r.empty else ""

    def _ret(n):
        return round((c.iloc[-1] / c.iloc[-1 - n] - 1) * 100, 2) if len(c) > n else None

    # 因子明细 + IC 贡献
    facs = {}
    for f, w in scorer.IC_WEIGHTS.items():
        val = registry.get(f).fn(df).iloc[-1]
        facs[f] = {"value": round(float(val), 4) if pd.notna(val) else None,
                   "weight": w, "desc": registry.get(f).desc}

    # 综合分与全市场排名
    if market_scores is None:
        market_scores = scorer.score_fast(codes=universe(), top=10000)
    score = rank = pct = None
    if not market_scores.empty and code in set(market_scores["code"]):
        ms = market_scores.reset_index(drop=True)
        score = round(float(ms.loc[ms["code"] == code, "score"].iloc[0]), 3)
        rank = int(ms.index[ms["code"] == code][0]) + 1
        pct = round((1 - rank / len(ms)) * 100, 1)

    lv = _levels(df)
    signals = {nm: ("持有" if fn(df).iloc[-1] == 1 else "空仓")
               for nm, fn in __import__("aquant.signal.timing", fromlist=["SIGNALS"]).SIGNALS.items()}

    ff = None
    if store.has_table("fund_flow"):
        fr = store.query("SELECT main_net, main_net_pct FROM fund_flow WHERE code=? ORDER BY date DESC LIMIT 1", [code])
        if not fr.empty:
            ff = {"main_net": float(fr["main_net"].iloc[0]), "main_net_pct": float(fr["main_net_pct"].iloc[0])}

    # 近期资讯 + 关键词识别利好/利空（规则化，无 LLM）
    news, catalysts, alerts = [], [], []
    try:
        if offline:
            from .data import research_cache
            news = research_cache.read_news(code)
        else:
            from .data.sources.news import stock_news
            news = stock_news(code, limit=8)
    except Exception:
        news = []
    _POS = ("中标", "回购", "增持", "预增", "扭亏", "新高", "合作", "获批", "订单", "分红", "重组")
    _NEG = ("减持", "预亏", "亏损", "立案", "处罚", "问询", "退市", "质押", "诉讼", "下滑", "商誉")
    for n in news:
        t = n.get("title", "")
        for k in _POS:
            if k in t and t not in catalysts:
                catalysts.append(t); break
        for k in _NEG:
            if k in t and t not in alerts:
                alerts.append(t); break

    # 基本面上下文（估值取缓存表；财务/筹码/分红实时，各自降级）
    val_row = {}
    if store.has_table("fundamental"):
        vr = store.query("SELECT pe,pb,total_mv,circ_mv,turnover FROM fundamental "
                         "WHERE code=? ORDER BY date DESC LIMIT 1", [code])
        if not vr.empty:
            val_row = {k: (float(vr[k].iloc[0]) if pd.notna(vr[k].iloc[0]) else None) for k in vr.columns}
    try:
        if offline:
            from .data import research_cache
            fctx = research_cache.read_context(code) or {
                "valuation": val_row, "financial": {}, "chip": {}, "dividend": {}}
        else:
            from .data.sources import fundamental as fund
            fctx = fund.context(code, valuation_row=val_row)
    except Exception:
        fctx = {"valuation": val_row, "financial": {}, "chip": {}, "dividend": {}}

    return {
        "code": code, "name": name, "date": df["date"].iloc[-1],
        "close": lv["close"], "pct_chg": float(df["pct_chg"].iloc[-1]) if "pct_chg" in df else None,
        "returns": {"5d": _ret(5), "20d": _ret(20), "60d": _ret(60), "250d": _ret(250)},
        "score": score, "rank": rank, "percentile": pct,
        "factors": facs, "levels": lv, "signals": signals, "fund_flow": ff,
        "fundamental": fctx,
        "news": news, "catalysts": catalysts, "alerts": alerts,
    }


def report_markdown(rep: dict) -> str:
    """把 stock_report 渲染成一页式 Markdown。"""
    if not rep:
        return "（无数据或历史不足）"
    r = rep["returns"]
    lv = rep["levels"]
    lines = [
        f"# {rep['code']} {rep['name']} 研投报告",
        f"*截至 {rep['date']}；多维：价量·因子·基本面·资金·筹码；仅供研究，不构成建议*", "",
        f"**现价 {rep['close']}**（{rep['pct_chg']:+.2f}%）　综合分 **{rep['score']}**　"
        f"全市场排名 **{rep['rank']}**（击败 {rep['percentile']}% 个股，越高越符合策略）", "",
        f"**区间表现**：5日 {r['5d']}% ｜ 20日 {r['20d']}% ｜ 60日 {r['60d']}% ｜ 250日 {r['250d']}%", "",
        "**关键价位**", "",
        f"| MA20 | MA60 | 支撑(20日低) | 压力(20日高) | 止损 | 趋势 |",
        f"|---|---|---|---|---|---|",
        f"| {lv['ma20']} | {lv['ma60']} | {lv['support']} | {lv['resistance']} | {lv['stop']} | "
        f"{'多头(价>MA60)' if lv['above_ma60'] else '空头(价<MA60)'} |", "",
        "**择时信号**：" + " ｜ ".join(f"{k}={v}" for k, v in rep["signals"].items()), "",
    ]
    # 基本面块
    fc = rep.get("fundamental", {})
    val, fin, chip, div = fc.get("valuation", {}), fc.get("financial", {}), fc.get("chip", {}), fc.get("dividend", {})
    if any([val, fin, chip, div]):
        lines += ["**基本面**", ""]
        if val and val.get("pe") is not None:
            mv = val.get("total_mv")
            lines.append(f"- 估值：PE {val.get('pe')} ｜ PB {val.get('pb')} ｜ 总市值 "
                         f"{mv/1e8:.0f}亿" if mv else f"- 估值：PE {val.get('pe')} ｜ PB {val.get('pb')}")
        if fin:
            rev_y = fin.get("revenue_yoy"); np_y = fin.get("net_profit_yoy")
            lines.append(f"- 财务({fin.get('report_period','')})：ROE {fin.get('roe')}% ｜ "
                         f"净利率 {fin.get('net_margin')}% ｜ 营收同比 {rev_y}% ｜ 净利同比 {np_y}% ｜ "
                         f"负债率 {fin.get('debt_ratio')}%")
        if chip and chip.get("profit_ratio") is not None:
            lines.append(f"- 筹码：获利盘 {chip['profit_ratio']*100:.0f}% ｜ 平均成本 {chip.get('avg_cost')} ｜ "
                         f"90集中度 {chip.get('concentration_90')}")
        if div and div.get("dividend_yield"):
            lines.append(f"- 分红：股息率 {div.get('dividend_yield')}%")
        lines.append("")
    if rep["fund_flow"]:
        ff = rep["fund_flow"]
        lines += [f"**主力资金**：净流入 {ff['main_net']/1e8:+.2f} 亿（占比 {ff['main_net_pct']:+.2f}%）", ""]
    # 资讯面
    if rep.get("catalysts") or rep.get("alerts") or rep.get("news"):
        lines += ["**资讯面**", ""]
        if rep.get("catalysts"):
            lines.append("- 🟢 潜在利好：" + "；".join(rep["catalysts"][:3]))
        if rep.get("alerts"):
            lines.append("- 🔴 风险信号：" + "；".join(rep["alerts"][:3]))
        if rep.get("news"):
            lines.append("- 近期新闻：")
            lines += [f"  - {n.get('time','')[:10]} {n.get('title','')}（{n.get('source','')}）"
                      for n in rep["news"][:5]]
        lines.append("")
    lines += ["**因子明细（IC加权）**", "", "| 因子 | 值 | 权重 | 含义 |", "|---|---|---|---|"]
    for f, d in rep["factors"].items():
        lines.append(f"| {f} | {d['value']} | {d['weight']:+.2f} | {d['desc']} |")
    return "\n".join(lines)


def decision(code: str, rep: dict | None = None, offline: bool = False) -> dict:
    """决策仪表盘：把多维数据融合成可执行结论。

    哲学锚定已验证的策略——低波 + 反转 + 季度持有；基本面做质量校验，
    资金/筹码做确认，技术位给买卖点。输出 核心结论 + 作战计划 + 风险。
    """
    rep = rep or stock_report(code, offline=offline)
    if not rep:
        return {}
    fc = rep.get("fundamental", {})
    fin, val, chip = fc.get("financial", {}), fc.get("valuation", {}), fc.get("chip", {})
    lv, r = rep["levels"], rep["returns"]

    # —— 综合评分 0~100（四档加权）——
    parts, notes = {}, []
    # 1) 策略契合度（IC 排名分位）40
    pct = rep.get("percentile") or 0
    parts["策略契合"] = round(pct * 0.40, 1)
    # 2) 基本面质量 30
    q = 0
    roe = fin.get("roe")
    if roe is not None:
        q += 12 if roe >= 12 else 8 if roe >= 6 else 3 if roe >= 0 else 0
    if fin.get("revenue_yoy") is not None and fin.get("net_profit_yoy") is not None:
        if fin["revenue_yoy"] > 0 and fin["net_profit_yoy"] > 0:
            q += 12
        elif fin["net_profit_yoy"] < -30:
            q += 0; notes.append("净利大幅下滑")
        else:
            q += 5
    dr = fin.get("debt_ratio")
    is_fin = any(k in (rep.get("name") or "") for k in ("银行", "证券", "保险"))  # 金融股负债率天然高
    if dr is not None and not is_fin:
        q += 6 if dr < 60 else 3 if dr < 80 else 0
    elif is_fin:
        q += 6  # 金融股不以负债率扣分
    parts["基本面"] = round(min(q, 30), 1)
    # 3) 资金/筹码确认 15
    cf = 0
    ff = rep.get("fund_flow")
    if ff:
        cf += 8 if ff["main_net"] > 0 else 2
    if chip.get("profit_ratio") is not None:
        cf += 7 if chip["profit_ratio"] < 0.5 else 3  # 获利盘低=套牢盘少=上方压力小
    parts["资金筹码"] = round(min(cf, 15), 1)
    # 4) 估值合理 15
    v = 7.5
    pe = val.get("pe")
    if pe is not None:
        v = 13 if 0 < pe <= 30 else 9 if 30 < pe <= 60 else 3 if pe > 60 else 2  # 负PE=亏损
        if pe is not None and pe <= 0:
            notes.append("亏损(PE<0)")
    parts["估值"] = round(v, 1)
    total = round(sum(parts.values()), 1)

    # —— 市场状态注入（自上而下）：防守期压低个股积极度 ——
    mkt_state = None
    try:
        from . import market
        mkt_state = (market.regime() or {}).get("state")
    except Exception:
        pass
    if mkt_state == "防守":
        total = round(total * 0.85, 1)  # 大盘防守，个股整体降温
        notes.append("大盘防守期")

    # —— 核心结论 ——
    if total >= 65:
        signal, advice_no, advice_has = "买入/增持", "可分批建仓", "继续持有"
    elif total >= 50:
        signal, advice_no, advice_has = "持有/观望", "等回踩或确认企稳再介入", "持有，跌破止损减仓"
    else:
        signal, advice_no, advice_has = "回避/减持", "暂不介入", "逢反弹减仓"
    if mkt_state:
        advice_no += f"（大盘{mkt_state}）"

    # 时间敏感度：临近支撑/止损更敏感
    near_stop = lv["close"] <= lv["stop"] * 1.03
    sensitivity = "高（临近止损）" if near_stop else "一般"

    one_liner = (f"综合 {total} 分（{signal}）：策略契合{('强' if pct>70 else '中' if pct>40 else '弱')}，"
                 f"{'基本面稳健' if parts['基本面']>=20 else '基本面一般'}，"
                 f"{'主力净流入' if (ff and ff['main_net']>0) else '主力流出/无数据'}。")

    # —— 风险提示 + 风险等级 ——
    risks, severe = list(notes), 0
    if fin.get("net_profit_yoy") is not None and fin["net_profit_yoy"] < -30:
        severe += 1  # notes 里已记"净利大幅下滑"
    if fin.get("revenue_yoy") is not None and fin["revenue_yoy"] < -10:
        risks.append(f"营收下滑({fin['revenue_yoy']}%)"); severe += 1
    if roe is not None and roe < 0:
        risks.append("ROE为负(亏损)"); severe += 1
    if pe is not None and pe <= 0:
        severe += 1  # notes 里已记"亏损(PE<0)"
    if pe is not None and pe > 80:
        risks.append(f"估值偏高(PE {pe})")
    if not lv["above_ma60"]:
        risks.append("中期趋势偏弱(价<MA60)")
    if ff and ff["main_net"] < 0:
        risks.append(f"主力净流出 {ff['main_net']/1e8:.2f}亿")
    if dr is not None and dr > 80 and not is_fin:
        risks.append(f"高负债({dr}%)"); severe += 1
    if near_stop:
        risks.append("已接近机械止损位"); severe += 1
    for a in (rep.get("alerts") or [])[:2]:  # 资讯风险信号
        risks.append(f"资讯: {a[:24]}"); severe += 1
    risk_level = "高" if severe >= 2 else "中" if (severe == 1 or len(risks) >= 3) else "低"

    # —— 作战计划（买卖点）——
    plan = {
        "ideal_buy": round(min(lv["ma20"], lv["close"]) * 0.99, 2),  # 回踩 MA20/现价下沿
        "secondary_buy": lv["support"],                               # 跌到支撑加仓
        "stop_loss": lv["stop"],
        "take_profit": lv["resistance"],
        "position": ("3~5成分批" if total >= 65 else "1~2成试探" if total >= 50 else "0（不建仓）"),
    }
    checklist = [
        f"本策略为季度持有，触发买入后持有约一季度再按分数评估换仓",
        f"跌破止损 {plan['stop_loss']} 无条件减仓",
        f"涨至压力 {plan['take_profit']} 附近分批止盈/观察放量",
    ]
    if signal.startswith("回避"):
        checklist = ["综合分偏低，不符合当前策略，建议观望或回避", f"若已持有，逢反弹至 {lv['ma20']} 附近减仓"]

    return {
        "code": code, "name": rep["name"], "date": rep["date"], "close": lv["close"],
        "total_score": total, "score_parts": parts, "signal": signal,
        "one_liner": one_liner, "sensitivity": sensitivity,
        "advice": {"no_position": advice_no, "has_position": advice_has},
        "risk_level": risk_level, "risks": risks or ["无显著风险信号"],
        "battle_plan": plan, "checklist": checklist, "report": rep,
    }


def briefing(top: int = 12, weights: dict | None = None) -> pd.DataFrame:
    """荐股研报快览：对 IC 候选池逐只跑多维决策，汇成一张速览表。

    把"选股(IC) → 多维研判(基本面/资金/风险/资讯)"打通，一眼看清每只候选的
    综合分、信号、风险等级、利好利空、买卖点。
    """
    from .select import scorer
    codes = universe()
    ranked = scorer.score_fast(codes=codes, top=top) if hasattr(scorer, "score_fast") \
        else scorer.score(codes, weights=weights, top=top)
    ms = scorer.score_fast(codes=codes, top=10000) if hasattr(scorer, "score_fast") else ranked
    rows = []
    for code in ranked["code"].tolist():
        rep = stock_report(code, market_scores=ms)
        d = decision(code, rep=rep)
        if not d:
            continue
        lv = d["battle_plan"]
        rows.append({
            "code": d["code"], "name": d["name"], "综合分": d["total_score"],
            "信号": d["signal"], "风险": d.get("risk_level", "-"),
            "现价": d["close"], "买点": lv["ideal_buy"], "止损": lv["stop_loss"], "目标": lv["take_profit"],
            "利好": "；".join((rep.get("catalysts") or [])[:3]),
            "利空": "；".join((rep.get("alerts") or [])[:3]),
        })
    return pd.DataFrame(rows)


def dashboard_markdown(d: dict) -> str:
    """决策仪表盘 → Markdown（核心结论在最上，细节在下）。"""
    if not d:
        return "（无数据或历史不足）"
    p = d["battle_plan"]
    sig_icon = {"买入/增持": "🟢", "持有/观望": "🟡", "回避/减持": "🔴"}.get(d["signal"], "")
    parts = " + ".join(f"{k}{v}" for k, v in d["score_parts"].items())
    lines = [
        f"# {d['code']} {d['name']} 决策仪表盘",
        f"*截至 {d['date']}；多维融合；仅供研究，不构成投资建议*", "",
        f"## {sig_icon} 核心结论：{d['signal']}（综合 {d['total_score']} 分）", "",
        f"> {d['one_liner']}", "",
        f"- **评分构成**：{parts}",
        f"- **时间敏感度**：{d['sensitivity']}",
        f"- **未持仓**：{d['advice']['no_position']}　|　**已持仓**：{d['advice']['has_position']}", "",
        f"## ⚔️ 作战计划", "",
        f"| 理想买点 | 次选买点 | 止损 | 目标 | 建议仓位 |",
        f"|---|---|---|---|---|",
        f"| {p['ideal_buy']} | {p['secondary_buy']} | {p['stop_loss']} | {p['take_profit']} | {p['position']} |", "",
        "**操作清单**", "",
    ] + [f"- {c}" for c in d["checklist"]] + [
        "", f"## ⚠️ 风险等级：{d.get('risk_level','-')}", "",
    ] + [f"- {r}" for r in d["risks"]] + ["", "---", "", report_markdown(d["report"])]
    return "\n".join(lines)


_ACTION_ICON = {"买入": "🟢买入", "持有": "🟡持有", "卖出": "🔴卖出", "空仓": "⚪空仓"}


def to_markdown(picks: pd.DataFrame, signal: str = "ma_cross") -> str:
    """渲染为可读的决策清单 Markdown。"""
    if picks.empty:
        return ("## 每日建仓名单\n\n"
                "今日无候选（仓库数据不足或满足最小历史的标的过少）。")
    asof = picks["signal_date"].iloc[0] if "signal_date" in picks else ""
    n = len(picks)
    lines = [f"## 每日建仓名单（综合分 Top{n}，截至 {asof}）", "",
             "> 综合分最高的低波/反转标的即今日建仓名单（契合季度换仓策略）；"
             "「趋势」列为 " + signal + " 择时参考，非建仓依据。",
             "> 仅供研究参考，不构成投资建议。`stop` 为机械止损参考位。", "",
             "| 排名 | 代码 | 名称 | 综合分 | 趋势 | 现价 | MA20 | MA60 | 支撑 | 压力 | 止损 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(picks.itertuples(index=False), 1):
        act = _ACTION_ICON.get(r.action, r.action)
        lines.append(f"| {i} | {r.code} | {r.name} | {r.score} | {act} | "
                     f"{r.close} | {r.ma20} | {r.ma60} | {r.support} | {r.resistance} | {r.stop} |")
    return "\n".join(lines)
