import pandas as pd
import pytest

from aquant import analysts


@pytest.fixture()
def seed(seed_db):
    # 龙虎榜席位 + 大盘情绪，供资金面/消息面分析师取用
    seed_db.save("lhb_detail", pd.DataFrame([
        {"code": "600000", "name": "浦发银行", "date": "2026-07-03", "reason": "涨幅偏离",
         "close": 10.0, "pct_chg": 9.9, "lhb_net_buy": 5e7, "lhb_amount": 2e8}]))
    seed_db.save("lhb_seat", pd.DataFrame([
        {"code": "600000", "date": "2026-07-03", "side": "buy", "rank": 1, "seat": "机构专用",
         "buy": 3e7, "sell": 0.0, "net": 3e7, "seat_type": "inst", "hotmoney_name": None}]))
    seed_db.save("market_news", pd.DataFrame([
        {"time": "2026-07-05 09:00", "title": "央行降准", "summary": "利好", "url": "http://a", "sent": 1}]))
    return seed_db


def test_ai_research_structure_with_llm(seed):
    calls = []

    def fake_chat(prompt, timeout=120):
        calls.append(prompt)
        return f"LLM观点{len(calls)}"

    r = analysts.ai_research("600000", offline=True, chat=fake_chat)
    assert r["code"] == "600000"
    assert set(r["analysts"]) == {"technical", "capital", "news", "fundamental"}
    assert all(r["analysts"][k] for k in r["analysts"])
    assert r["debate"]["bull"] and r["debate"]["bear"]
    assert r["verdict"]["stance"]  # 规则给出的操作倾向
    assert r["verdict"]["risks"]
    assert r["llm_used"] is True
    assert len(calls) == 6  # 4 分析师 + 多 + 空


def test_ai_research_degrades_without_llm(seed):
    r = analysts.ai_research("600000", offline=True, chat=lambda *a, **k: None)
    # 无 LLM 也返回完整结构（规则文本）
    assert set(r["analysts"]) == {"technical", "capital", "news", "fundamental"}
    assert all(r["analysts"][k] for k in r["analysts"])
    assert r["debate"]["bull"] and r["debate"]["bear"]
    assert r["verdict"]["stance"]
    assert r["llm_used"] is False


def test_capital_view_mentions_lhb(seed):
    r = analysts.ai_research("600000", offline=True, chat=lambda *a, **k: None)
    # 规则降级时资金面文本应体现龙虎榜（有机构席位）
    assert "龙虎榜" in r["analysts"]["capital"] or "机构" in r["analysts"]["capital"]
