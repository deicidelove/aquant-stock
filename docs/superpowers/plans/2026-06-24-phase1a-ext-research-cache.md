# Phase 1A-ext — 研投缓存层（新闻/筹码预取）+ 离线研判报告 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 消除 `/api/stock/{code}/report` 端点的请求内联网（终审 Critical）：把新闻/财务/筹码改为后台预取落库、端点只读缓存，既守住"处理器不联网"铁律又保留完整 report 内容。

**Architecture:** 缓存表的 DB 读写放 `aquant/data/research_cache.py`（纯 DuckDB，无网络，避免 aquant→server 循环依赖）；预取编排（akshare 抓取 + 写缓存）放 `server/refresh/research_cache.py`，挂到收盘后 EOD 调度任务。`stock_report`/`decision` 新增 `offline` 模式：offline 时读缓存而非实时抓。API report 端点用 `offline=True`。

**Tech Stack:** Python 3.11 · FastAPI · DuckDB（`aquant.data.store`）· APScheduler · pytest。复用 `aquant.data.sources.news.stock_news`、`aquant.data.sources.fundamental.context`、`server.refresh.scores.read_top_scores`、`aquant.research.daily_picks`。

## Global Constraints

- 分层铁律：`aquant/` 不得 import `server/`（server 依赖 aquant，反向会循环）。缓存 DB 读写归 `aquant/data/research_cache.py`；只有"抓第三方数据"的编排归 `server/refresh/`。
- API 请求处理器内禁止任何第三方网络调用；report 端点必须走 `offline=True`（只读缓存表）。
- 新建表在 `aquant/data/store.py` 的 `TABLE_KEYS` 注册主键。
- 缓存按 `(code, as_of)` 存，`as_of = store.max_date("daily_bar")`；同日重抓幂等覆盖。新闻与上下文各存为一行 JSON blob（列 `news_json` / `ctx_json`，均为 JSON 字符串）。
- 预取范围 = 驾驶舱可见集合：`read_top_scores(top=120)` 的 code ∪ `daily_picks()` 的 code（去重）。未命中股 report 优雅降级（无新闻/筹码，仍有评分/价位/已缓存估值）。
- `stock_report`/`decision` 默认 `offline=False`，保持现有 CLI/dashboard 行为不变。
- 测试用 conftest 的 `seed_db`/`client` fixture（临时 DuckDB），注入假 fetch，不联网。
- 提交信息结尾：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。分支：`phase1a-backend`（续用，不新建）。

---

### Task E1: 缓存表 DB 读写层 `aquant/data/research_cache.py`

**Files:**
- Create: `aquant/data/research_cache.py`
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `news_cache`、`fund_context_cache`）
- Test: `tests/test_research_cache.py`

**Interfaces:**
- Produces（均为纯 DuckDB，无网络）:
  - `save_news(code: str, as_of: str, items: list[dict]) -> int`（写 `news_cache` 一行，返回写入行数=1；items 存为 `news_json`）
  - `save_context(code: str, as_of: str, ctx: dict) -> int`（写 `fund_context_cache` 一行，`ctx` 存为 `ctx_json`）
  - `read_news(code: str) -> list[dict]`（读该 code 最新 as_of 的新闻列表；无则 `[]`）
  - `read_context(code: str) -> dict`（读该 code 最新 as_of 的上下文 dict；无则 `{}`）

- [ ] **Step 1: 注册表主键**

`aquant/data/store.py` 的 `TABLE_KEYS` 字典内新增两行：
```python
    "news_cache": ["code", "as_of"],
    "fund_context_cache": ["code", "as_of"],
```

- [ ] **Step 2: 写失败测试**

`tests/test_research_cache.py`：
```python
def test_news_roundtrip(seed_db):
    from aquant.data import research_cache as rc
    items = [{"title": "公司中标大单", "time": "2026-06-23 09:00:00", "source": "东财"}]
    n = rc.save_news("600000", "2026-06-23", items)
    assert n == 1
    assert rc.read_news("600000") == items
    assert rc.read_news("000001") == []  # 未缓存 → 空


def test_context_roundtrip(seed_db):
    from aquant.data import research_cache as rc
    ctx = {"valuation": {"pe": 5.1}, "financial": {"roe": 12.3},
           "chip": {"profit_ratio": 0.8}, "dividend": {"dividend_yield": 3.2}}
    rc.save_context("600000", "2026-06-23", ctx)
    assert rc.read_context("600000") == ctx
    assert rc.read_context("000001") == {}
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_research_cache.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'aquant.data.research_cache'`）

- [ ] **Step 4: 实现 `research_cache.py`**

`aquant/data/research_cache.py`：
```python
"""研投缓存表（新闻/财务筹码上下文）的纯 DuckDB 读写。

数据由 server.refresh.research_cache 后台预取写入；此模块只做落库与读取，
不触网，供 aquant.research 离线读取（避免 aquant→server 反向依赖）。
按 (code, as_of) 存，各存一行 JSON blob。
"""
from __future__ import annotations

import json

import pandas as pd

from . import store


def save_news(code: str, as_of: str, items: list[dict]) -> int:
    df = pd.DataFrame([{"code": code, "as_of": as_of,
                        "news_json": json.dumps(items, ensure_ascii=False)}])
    return store.save("news_cache", df)


def save_context(code: str, as_of: str, ctx: dict) -> int:
    df = pd.DataFrame([{"code": code, "as_of": as_of,
                        "ctx_json": json.dumps(ctx, ensure_ascii=False)}])
    return store.save("fund_context_cache", df)


def read_news(code: str) -> list[dict]:
    if not store.has_table("news_cache"):
        return []
    df = store.query("SELECT news_json FROM news_cache WHERE code=? "
                     "ORDER BY as_of DESC LIMIT 1", [code])
    return json.loads(df["news_json"].iloc[0]) if not df.empty else []


def read_context(code: str) -> dict:
    if not store.has_table("fund_context_cache"):
        return {}
    df = store.query("SELECT ctx_json FROM fund_context_cache WHERE code=? "
                     "ORDER BY as_of DESC LIMIT 1", [code])
    return json.loads(df["ctx_json"].iloc[0]) if not df.empty else {}
```

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_research_cache.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add aquant/data/research_cache.py aquant/data/store.py tests/test_research_cache.py
git commit -m "feat(data): 研投缓存表 news_cache/fund_context_cache 读写层

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task E2: 后台预取任务 `prefetch_research` + 挂到 EOD 调度

**Files:**
- Create: `server/refresh/research_cache.py`
- Modify: `server/refresh/scheduler.py`（`_eod_job` 末尾追加预取调用）
- Test: `tests/test_prefetch.py`

**Interfaces:**
- Consumes: `aquant.data.research_cache.save_news/save_context`（E1）；`server.refresh.scores.read_top_scores`；`aquant.research.daily_picks`；`aquant.data.store.max_date`；默认抓取 `aquant.data.sources.news.stock_news`、`aquant.data.sources.fundamental.context`
- Produces:
  - `server.refresh.research_cache.prefetch_universe(top: int = 120) -> list[str]`（read_top_scores(top) 的 code ∪ daily_picks() 的 code，去重排序）
  - `server.refresh.research_cache.prefetch_research(codes=None, news_fetch=None, ctx_fetch=None) -> int`（对每只抓新闻+上下文并写缓存，返回成功缓存的 code 数；`codes` 缺省用 `prefetch_universe()`；`news_fetch`/`ctx_fetch` 可注入替身）

- [ ] **Step 1: 写失败测试**

`tests/test_prefetch.py`：
```python
def test_prefetch_writes_cache(seed_db, monkeypatch):
    from server.refresh import research_cache as pf
    from aquant.data import research_cache as rc

    # 限定 universe 为 fixture 里的 code，避免依赖打分结果
    monkeypatch.setattr(pf, "prefetch_universe", lambda top=120: ["600000"])
    news = [{"title": "中标", "time": "2026-06-23", "source": "东财"}]
    ctx = {"valuation": {"pe": 5.0}, "financial": {}, "chip": {}, "dividend": {}}

    n = pf.prefetch_research(news_fetch=lambda c: news, ctx_fetch=lambda c: ctx)
    assert n == 1
    assert rc.read_news("600000") == news
    assert rc.read_context("600000") == ctx


def test_prefetch_universe_union(seed_db, monkeypatch):
    from server.refresh import research_cache as pf
    import pandas as pd
    from server.refresh import scores
    from aquant import research
    monkeypatch.setattr(scores, "read_top_scores",
                        lambda top=120: pd.DataFrame({"code": ["600000"], "name": ["x"],
                                                      "score": [1.0], "as_of": ["2026-06-23"]}))
    monkeypatch.setattr(research, "daily_picks",
                        lambda **k: pd.DataFrame({"code": ["000001"], "name": ["y"], "score": [2.0]}))
    assert pf.prefetch_universe() == ["000001", "600000"]
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_prefetch.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server.refresh.research_cache'`）

- [ ] **Step 3: 实现 `server/refresh/research_cache.py`**

```python
"""研投缓存预取：盘后给驾驶舱可见集合（高分+建仓名单）抓新闻/财务筹码落库。

只在后台运行；抓取失败按 code 降级（不影响其他）。读取在 aquant.data.research_cache。
"""
from __future__ import annotations

from aquant.data import store
from aquant.data import research_cache as rc
from aquant.data.sources.news import stock_news
from aquant.data.sources import fundamental as fund
from aquant import research
from server.refresh import scores


def prefetch_universe(top: int = 120) -> list[str]:
    """驾驶舱可见集合：高分 Top-N 的 code ∪ 每日建仓名单的 code。"""
    codes: set[str] = set()
    s = scores.read_top_scores(top=top)
    if not s.empty:
        codes |= set(s["code"])
    p = research.daily_picks()
    if not p.empty:
        codes |= set(p["code"])
    return sorted(codes)


def prefetch_research(codes=None, news_fetch=None, ctx_fetch=None) -> int:
    """对集合内每只抓新闻+上下文写缓存，返回成功缓存的 code 数。"""
    codes = codes if codes is not None else prefetch_universe()
    news_fetch = news_fetch or (lambda c: stock_news(c, limit=8))
    ctx_fetch = ctx_fetch or (lambda c: fund.context(c))
    as_of = store.max_date("daily_bar")
    if as_of is None or not codes:
        return 0
    done = 0
    for code in codes:
        try:
            rc.save_news(code, as_of, news_fetch(code) or [])
            rc.save_context(code, as_of, ctx_fetch(code) or {})
            done += 1
        except Exception:  # noqa: BLE001 单只失败降级，不影响其他
            continue
    return done
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_prefetch.py -v`
Expected: PASS

- [ ] **Step 5: 挂到 EOD 调度任务**

`server/refresh/scheduler.py` 的 `_eod_job` 函数体改为（在 materialize 后追加预取；保持各自 try/except 降级）：
```python
def _eod_job() -> None:
    try:
        scores.materialize_scores()
    except Exception:  # noqa: BLE001
        pass
    try:
        from server.refresh.research_cache import prefetch_research
        prefetch_research()
    except Exception:  # noqa: BLE001
        pass
```
（`scores` 已在 scheduler.py 顶部导入；prefetch_research 用函数内延迟导入避免循环。）

- [ ] **Step 6: 回归 + 提交**

Run: `python3 -m pytest tests/test_prefetch.py tests/test_scheduler.py -v`
Expected: PASS

```bash
git add server/refresh/research_cache.py server/refresh/scheduler.py tests/test_prefetch.py
git commit -m "feat(refresh): 研投缓存预取 prefetch_research + 挂 EOD 调度

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task E3: `stock_report`/`decision` 离线模式 + report 端点改用缓存

**Files:**
- Modify: `aquant/research.py`（`stock_report` 与 `decision` 加 `offline` 参数）
- Modify: `server/routers/stock.py`（report 端点传 `offline=True`）
- Test: `tests/test_offline_report.py`（新）；`tests/test_stock_api.py`（改 report 用例走真实离线路径）

**Interfaces:**
- Consumes: `aquant.data.research_cache.read_news/read_context`（E1）
- Produces:
  - `aquant.research.stock_report(code, market_scores=None, offline: bool = False) -> dict`（offline=True 时新闻读 `research_cache.read_news`、基本面上下文读 `research_cache.read_context`，均不触网；cache 缺失则降级为空）
  - `aquant.research.decision(code, rep=None, offline: bool = False) -> dict`（rep 为 None 时以 `offline` 调 stock_report）
  - report 端点 `GET /api/stock/{code}/report` 内部调用 `research.decision(code, offline=True)`

- [ ] **Step 1: 写失败测试（离线读缓存 + 证明不触网）**

`tests/test_offline_report.py`：
```python
def test_stock_report_offline_reads_cache(seed_db, monkeypatch):
    from aquant import research
    from aquant.data import research_cache as rc
    from aquant.data.sources import news as news_mod
    from aquant.data.sources import fundamental as fund

    rc.save_news("600000", "2026-04-22", [{"title": "离线缓存新闻", "time": "2026-04-22", "source": "东财"}])
    rc.save_context("600000", "2026-04-22",
                    {"valuation": {"pe": 5.0}, "financial": {}, "chip": {}, "dividend": {}})

    # 离线路径绝不调用实时抓取：调用即让测试失败
    def _boom(*a, **k):
        raise AssertionError("offline 路径不应触网")
    monkeypatch.setattr(news_mod, "stock_news", _boom)
    monkeypatch.setattr(fund, "context", _boom)

    rep = research.stock_report("600000", offline=True)
    assert rep
    assert rep["news"] == [{"title": "离线缓存新闻", "time": "2026-04-22", "source": "东财"}]
    assert rep["fundamental"]["valuation"]["pe"] == 5.0
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_offline_report.py -v`
Expected: FAIL（`stock_report() got an unexpected keyword argument 'offline'`）

- [ ] **Step 3: 改 `stock_report` 支持 offline**

`aquant/research.py`：把 `def stock_report(code: str, market_scores: pd.DataFrame | None = None) -> dict:`
改为 `def stock_report(code: str, market_scores: pd.DataFrame | None = None, offline: bool = False) -> dict:`

把现有「近期资讯」抓取块（`news = []` 起、含 `from .data.sources.news import stock_news` 与 `news = stock_news(code, limit=8)`）替换为：
```python
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
```

把现有「基本面上下文」里 `fctx` 的实时抓取块（含 `from .data.sources import fundamental as fund` 与 `fctx = fund.context(code, valuation_row=val_row)`）替换为：
```python
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
```

- [ ] **Step 4: 改 `decision` 透传 offline**

`aquant/research.py`：把 `def decision(code: str, rep: dict | None = None) -> dict:`
改为 `def decision(code: str, rep: dict | None = None, offline: bool = False) -> dict:`
并把函数内 `rep = rep or stock_report(code)` 改为 `rep = rep or stock_report(code, offline=offline)`。

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_offline_report.py -v`
Expected: PASS

- [ ] **Step 6: report 端点改用离线 + 改测试走真实路径**

`server/routers/stock.py` 把 `d = research.decision(code)` 改为 `d = research.decision(code, offline=True)`。

`tests/test_stock_api.py` 把现有 `test_report` 替换为真实离线路径（不再 mock decision；seed 缓存并断言命中缓存内容，同时证明不触网）：
```python
def test_report_offline(client, seed_db, monkeypatch):
    from aquant.data import research_cache as rc
    from aquant.data.sources import news as news_mod
    from aquant.data.sources import fundamental as fund
    rc.save_news("600000", "2026-04-22", [{"title": "缓存新闻", "time": "2026-04-22", "source": "东财"}])
    rc.save_context("600000", "2026-04-22", {"valuation": {}, "financial": {}, "chip": {}, "dividend": {}})
    monkeypatch.setattr(news_mod, "stock_news", lambda *a, **k: (_ for _ in ()).throw(AssertionError("不应触网")))
    monkeypatch.setattr(fund, "context", lambda *a, **k: (_ for _ in ()).throw(AssertionError("不应触网")))
    r = client.get("/api/stock/600000/report")
    assert r.status_code == 200
    assert r.json()["code"] == "600000"
    assert r.json()["decision"]
```

- [ ] **Step 7: 全量回归**

Run: `python3 -m pytest -v`
Expected: PASS（含全部既有用例 + 新增；report 端点走真实离线缓存路径、无网络）

- [ ] **Step 8: 提交**

```bash
git add aquant/research.py server/routers/stock.py tests/test_offline_report.py tests/test_stock_api.py
git commit -m "feat(report): stock_report/decision 离线模式 + report 端点只读缓存

修复终审 Critical：report 端点不再请求内联网。

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**：
- 消除 report 端点请求内联网（终审 Critical）→ Task E3（端点走 offline，读缓存）。✅
- 缓存层无 aquant→server 循环依赖 → Task E1 读写在 `aquant/data/`，编排在 `server/refresh/`。✅
- 预取范围=驾驶舱可见集合（高分∪建仓名单）→ Task E2 `prefetch_universe`。✅
- 后台预取落库、未命中降级 → E2 写缓存 + E3 offline 缺失返回空。✅
- 默认 offline=False 保持旧行为 → E3 参数默认值。✅

**占位符扫描**：无 TBD/TODO；每步含完整代码。✅

**类型一致性**：`save_news/save_context(...)->int`、`read_news(...)->list[dict]`、`read_context(...)->dict`、`prefetch_universe(top)->list[str]`、`prefetch_research(...)->int`、`stock_report(...,offline:bool=False)`、`decision(...,offline:bool=False)` 在各任务间一致；E2 写、E3 读同一对 `read_news/read_context` 契约。✅

**范围**：聚焦"缓存层 + 离线 report"单一目标，3 个 TDD 任务，pytest 可测。✅
