"""AI 多智能体投研报告。

设计：规则给硬决策（操作倾向/仓位/风险，来自 research.decision，确定可靠），
LLM 给叙事（4 位分析师观点 + 多空辩论）。LLM 不可用则规则文本降级，结构不变。

LLM 调用是网络 → 仅异步任务应传 offline=False；请求路径只读缓存。
"""
from __future__ import annotations

from typing import Callable

from . import llm, research, sentiment
from . import lhb as lhb_mod


def _fmt_pct(v) -> str:
    return "-" if v is None else f"{v:.1f}%"


def _facts(rep: dict, dec: dict, lhb_data: dict, mkt: dict) -> dict[str, str]:
    """把结构化数据拼成各分析师的事实串（也用作规则降级文本的基础）。"""
    lv, r = rep.get("levels", {}), rep.get("returns", {})
    trend = "多头排列" if lv.get("above_ma60") else "空头/震荡"
    tech = (f"现价{lv.get('close')}，MA20 {lv.get('ma20')} / MA60 {lv.get('ma60')}，{trend}；"
            f"支撑{lv.get('support')} 压力{lv.get('resistance')}；"
            f"区间涨跌 5日{_fmt_pct(r.get('5d'))} 20日{_fmt_pct(r.get('20d'))} 60日{_fmt_pct(r.get('60d'))}；"
            f"综合分{dec.get('total_score')}（{dec.get('signal')}）")

    ff = rep.get("fund_flow")
    cap_parts = []
    if ff:
        cap_parts.append(f"主力资金净流入{ff['main_net']/1e8:.2f}亿")
    buy, sell = lhb_data.get("buy", []), lhb_data.get("sell", [])
    if buy or sell:
        seats = buy + sell
        types = {s["seat_type"] for s in seats}
        tags = []
        if "inst" in types:
            tags.append("机构专用")
        if "north" in types:
            tags.append("北向")
        hot = [s["hotmoney_name"] for s in seats if s.get("hotmoney_name")]
        tags += hot
        cap_parts.append(f"上榜龙虎榜（{lhb_data.get('date')}），席位含{('、'.join(tags) or '普通营业部')}")
    cap = "；".join(cap_parts) or "近期无主力资金异动、未上龙虎榜"

    cats, alerts = rep.get("catalysts", []), rep.get("alerts", [])
    news_parts = []
    if cats:
        news_parts.append("个股利好：" + "；".join(cats[:3]))
    if alerts:
        news_parts.append("个股利空：" + "；".join(alerts[:3]))
    news_parts.append(f"大盘消息面情绪{mkt.get('score')}（{mkt.get('label')}）")
    news = "；".join(news_parts)

    fc = rep.get("fundamental", {})
    fin, val = fc.get("financial", {}), fc.get("valuation", {})
    fund_parts = []
    if fin:
        fund_parts.append(f"ROE {fin.get('roe')}% 营收同比{fin.get('revenue_yoy')}% 净利同比{fin.get('net_profit_yoy')}%")
    if val and val.get("pe") is not None:
        fund_parts.append(f"PE {val.get('pe')} PB {val.get('pb')}")
    fund = "；".join(fund_parts) or "基本面数据不足"

    return {"technical": tech, "capital": cap, "news": news, "fundamental": fund}


_ROLE = {
    "technical": "技术面分析师",
    "capital": "资金面分析师",
    "news": "消息面分析师",
    "fundamental": "基本面分析师",
}


def _analyst_prompt(role: str, name: str, code: str, fact: str) -> str:
    return (f"你是A股{_ROLE[role]}。仅从{_ROLE[role][:3]}角度，用不超过60字中文点评 {name}({code})，"
            f"给出观点和倾向，客观专业，不堆数据。\n数据：{fact}")


def _debate_prompt(side: str, name: str, code: str, facts: dict) -> str:
    stance = "看多" if side == "bull" else "看空"
    allf = "；".join(facts.values())
    return (f"你是A股{stance}研究员。基于以下多维数据，用不超过80字中文写出 {name}({code}) 的{stance}逻辑，"
            f"要有针对性、点出关键理由。\n数据：{allf}")


def ai_research(code: str, offline: bool = True,
                chat: Callable[..., str | None] | None = None) -> dict:
    """多智能体投研报告。offline=True 只读缓存（请求路径）；异步任务传 False 实网 LLM。"""
    chat = chat or llm.chat
    rep = research.stock_report(code, offline=offline)
    dec = research.decision(code, rep=rep, offline=offline)
    try:
        lhb_data = lhb_mod.lhb_stock(code)
    except Exception:  # noqa: BLE001
        lhb_data = {"buy": [], "sell": [], "date": None}
    try:
        mkt = sentiment.market_news_sentiment(limit=10)
    except Exception:  # noqa: BLE001
        mkt = {"score": 50, "label": "中性"}

    facts = _facts(rep, dec, lhb_data, mkt)
    name = rep.get("name", code)
    used = False

    analysts: dict[str, str] = {}
    for role, fact in facts.items():
        out = None
        try:
            out = chat(_analyst_prompt(role, name, code, fact))
        except Exception:  # noqa: BLE001
            out = None
        if out:
            used = True
            analysts[role] = out.strip()
        else:
            analysts[role] = fact  # 规则降级：直接给事实串

    debate: dict[str, str] = {}
    for side in ("bull", "bear"):
        out = None
        try:
            out = chat(_debate_prompt(side, name, code, facts))
        except Exception:  # noqa: BLE001
            out = None
        if out:
            used = True
            debate[side] = out.strip()
        else:
            debate[side] = _rule_debate(side, dec, facts)

    verdict = {
        "stance": dec.get("signal"),
        "reason": dec.get("one_liner"),
        "position": dec.get("battle_plan", {}).get("position"),
        "risks": dec.get("risks", []),
    }
    return {"code": code, "name": name, "as_of": rep.get("date"),
            "analysts": analysts, "debate": debate, "verdict": verdict,
            "llm_used": used}


def _rule_debate(side: str, dec: dict, facts: dict) -> str:
    """无 LLM 时的多空规则文本。"""
    sig = dec.get("signal", "")
    if side == "bull":
        return f"多头：{facts['technical']}。若资金面配合（{facts['capital']}），可期待延续。"
    return f"空头：注意风险 {('、'.join(dec.get('risks', [])) or '无显著')}；当前信号「{sig}」，追高需谨慎。"
