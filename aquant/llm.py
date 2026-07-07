"""LLM 综合研判：把多维结构化数据 + 资讯交给 Claude，生成自然语言投研意见。

直接调本地 `claude -p` CLI（订阅模式、免 API key），无需常驻代理服务。
取数/分析失败或 claude 不可用时优雅降级（返回 None），不影响其余功能。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request

CLAUDE_BIN = shutil.which("claude")
TIMEOUT = 60
OLLAMA_URL = os.getenv("AQUANT_OLLAMA_URL", "http://127.0.0.1:11434")


def available() -> bool:
    return CLAUDE_BIN is not None or bool(os.getenv("AQUANT_OLLAMA_MODEL"))


def _ollama_generate(prompt: str, model: str, timeout: int) -> str | None:
    """调本地 Ollama /api/generate（stdlib，零新依赖）。"""
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    out = (data.get("response") or "").strip()
    return out or None


def chat(prompt: str, timeout: int = 120) -> str | None:
    """provider 无关文本生成：Ollama(若配置) → claude -p → None。"""
    model = os.getenv("AQUANT_OLLAMA_MODEL")
    if model:
        try:
            out = _ollama_generate(prompt, model, timeout)
            if out:
                return out
        except Exception:  # noqa: BLE001 Ollama 不可用则回退
            pass
    return _ask(prompt)


def _ask(prompt: str) -> str | None:
    if not CLAUDE_BIN:
        return None
    try:
        r = subprocess.run([CLAUDE_BIN, "-p"], input=prompt, capture_output=True,
                           text=True, timeout=TIMEOUT)
        out = (r.stdout or "").strip()
        return out or None
    except Exception:
        return None


def _fmt_decision(d: dict, news: list[dict] | None) -> str:
    rep = d.get("report", {})
    fc = rep.get("fundamental", {})
    fin, val = fc.get("financial", {}), fc.get("valuation", {})
    lv, r = rep.get("levels", {}), rep.get("returns", {})
    ff = rep.get("fund_flow")
    parts = [
        f"股票：{d['code']} {d['name']}，现价 {d['close']}",
        f"量化综合分：{d['total_score']}/100（{d['signal']}），构成 {d['score_parts']}",
        f"风险等级：{d.get('risk_level')}；风险项：{'；'.join(d.get('risks', []))}",
        f"区间表现：5日{r.get('5d')}% 20日{r.get('20d')}% 60日{r.get('60d')}% 250日{r.get('250d')}%",
        f"技术：MA20 {lv.get('ma20')} MA60 {lv.get('ma60')} 支撑 {lv.get('support')} 压力 {lv.get('resistance')}；"
        f"趋势{'多头' if lv.get('above_ma60') else '空头'}",
    ]
    if fin:
        parts.append(f"财务：ROE {fin.get('roe')}% 营收同比 {fin.get('revenue_yoy')}% "
                     f"净利同比 {fin.get('net_profit_yoy')}% 负债率 {fin.get('debt_ratio')}%")
    if val and val.get("pe") is not None:
        parts.append(f"估值：PE {val.get('pe')} PB {val.get('pb')}")
    if ff:
        parts.append(f"主力资金：净流入 {ff['main_net']/1e8:.2f}亿")
    if news:
        parts.append("近期资讯：\n" + "\n".join(f"- {n.get('time','')[:10]} {n.get('title','')}" for n in news[:6]))
    return "\n".join(parts)


PROMPT = """你是资深A股投研分析师。基于以下多维数据，写一段 150 字以内的中文综合研判，包含：
1) 一句话核心逻辑（这只股票现在值不值得关注、为什么）；
2) 关键催化或风险（结合资讯）；
3) 明确的操作倾向（买入/观望/回避）与理由。
语气客观专业，不堆砌数据，给出判断。结尾标注"仅供研究，不构成投资建议"。

数据：
{data}
"""


def synthesize(decision: dict, news: list[dict] | None = None) -> str | None:
    """生成自然语言综合研判（失败返回 None）。"""
    if not decision:
        return None
    return _ask(PROMPT.format(data=_fmt_decision(decision, news)))
