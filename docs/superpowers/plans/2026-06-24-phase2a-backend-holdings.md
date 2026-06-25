# Phase 2A — 辅助股民后端（持仓 + 复盘）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现「我的持仓」手动交易记账（流水 CRUD + 持仓聚合 + 浮动盈亏 + 卖出提醒）与复盘端点（推荐记分卡 + 研报速览），全部只读库/无请求内联网。

**Architecture:** 领域纯函数放 `aquant/portfolio/holdings.py`（从 `trades` 表聚合持仓与盈亏，最新价取 `quote_snapshot`→回退 `daily_bar`，卖出提醒复用 `research.decision(offline=True)`）；FastAPI 路由薄封装。复盘复用 `track`/`research.briefing`（briefing 增加 offline 参数以守住不联网铁律）。

**Tech Stack:** Python 3.11 · FastAPI · DuckDB（`aquant.data.store`）· pytest + httpx TestClient。

## Global Constraints

- Python 3.11；复用现有 `aquant/` 领域核心，新增持仓逻辑放 `aquant/portfolio/`。
- DB 路径由环境变量 `AQUANT_DATA_DIR` 驱动；测试在 import 任何 `aquant` 模块**之前**设置该变量指向临时目录（沿用现有 `tests/conftest.py` 的做法）。
- 新表必须在 `aquant/data/store.py` 的 `TABLE_KEYS` 注册主键。`store.save(table, df)` 用 `INSERT OR REPLACE` 按主键 upsert；`store.query(sql, params)` 读。
- API 请求处理内**禁止**第三方网络调用；只允许 `store` 读写与复用领域函数（`decision`/`briefing` 必须以 `offline=True` 调用，避免 `stock_news`/`fundamental.context` 联网）。
- 写操作仅限 `trades` 表（POST/DELETE trade）；其余端点只读。
- 所有端点路径以 `/api` 前缀；JSON 响应用 pydantic 模型声明。
- 测试用 `httpx` + FastAPI `TestClient`，针对 conftest 注入的临时 DuckDB（含最小 `daily_bar`/`stock_basic` fixture，必要时注入 `trades`），不联网。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `phase2a-backend` 上开发（控制器在派发 Task 1 前建好）；每个 Task 末尾提交。
- 复用契约（现有代码）：
  - `aquant.research.decision(code, rep=None, offline=False) -> dict`，含 `battle_plan{stop_loss, take_profit, ...}`、`signal`（如 "买入/增持"/"持有/观望"/"回避/减持"）。
  - `aquant.research.briefing(top=12, weights=None) -> pd.DataFrame`，列：`code,name,综合分,信号,风险,现价,买点,止损,目标,利好,利空`（本计划 Task 4 给它加 `offline` 参数）。
  - `aquant.track.evaluate.forward_returns(horizons=(5,20,60)) -> pd.DataFrame`（台账明细 + `fwd_{h}`/`exc_{h}` 列；`picks_log` 为空时返回空 DataFrame）。
  - `aquant.data.store.save/query/has_table/max_date/load_daily`。

---

### Task 1: trades 表 + 持仓聚合服务（流水 CRUD + 盈亏）

**Files:**
- Create: `aquant/portfolio/__init__.py`, `aquant/portfolio/holdings.py`, `tests/test_holdings.py`
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `trades`）

**Interfaces:**
- Produces：
  - `aquant.portfolio.holdings.record_trade(date: str, code: str, side: str, shares: float, price: float, note: str = "") -> int`（写一行到 `trades`，`tid = 现有最大 tid + 1`（空表则 1），返回 tid）
  - `list_trades() -> pd.DataFrame`（按 tid 升序；空表返回空 DataFrame）
  - `delete_trade(tid: int) -> int`（删除该 tid，返回删除行数）
  - `_latest_price(code: str) -> float | None`（优先 `quote_snapshot` 最新 ts 的 close，回退 `daily_bar` 最新 close，无则 None）
  - `holdings() -> list[dict]`（当前在仓：每项 `{code, name, shares, avg_cost, last_price, market_value, unrealized, unrealized_pct}`；`shares>1e-9` 才算在仓）
  - `pnl_summary() -> dict`（`{realized, unrealized, total}`）

- [ ] **Step 1: 注册表主键**

`aquant/data/store.py` 的 `TABLE_KEYS` 字典内新增：
```python
    "trades": ["tid"],
```

- [ ] **Step 2: 写失败测试**

`tests/test_holdings.py`：
```python
import pandas as pd


def test_record_list_delete_trade(seed_db):
    from aquant.portfolio import holdings
    t1 = holdings.record_trade("2026-02-02", "600000", "buy", 1000, 10.0)
    t2 = holdings.record_trade("2026-02-03", "600000", "buy", 1000, 12.0)
    assert (t1, t2) == (1, 2)
    df = holdings.list_trades()
    assert len(df) == 2 and list(df["tid"]) == [1, 2]
    assert holdings.delete_trade(1) == 1
    assert list(holdings.list_trades()["tid"]) == [2]


def test_holdings_aggregation_and_pnl(seed_db):
    from aquant.portfolio import holdings
    # 600000 fixture 最新收盘 = 10 + 79*0.05 = 13.95
    holdings.record_trade("2026-02-02", "600000", "buy", 1000, 10.0)
    holdings.record_trade("2026-02-03", "600000", "buy", 1000, 12.0)  # 加权成本 11.0
    holdings.record_trade("2026-02-10", "600000", "sell", 500, 13.0)  # 已实现 (13-11)*500=1000
    pos = {h["code"]: h for h in holdings.holdings()}
    assert "600000" in pos
    h = pos["600000"]
    assert h["shares"] == 1500
    assert round(h["avg_cost"], 4) == 11.0
    assert h["last_price"] == 13.95
    assert round(h["unrealized"], 2) == round((13.95 - 11.0) * 1500, 2)
    s = holdings.pnl_summary()
    assert round(s["realized"], 2) == 1000.0
    assert round(s["total"], 2) == round(s["realized"] + s["unrealized"], 2)
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_holdings.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'aquant.portfolio'`）

- [ ] **Step 4: 实现 `holdings.py`**

`aquant/portfolio/holdings.py`：
```python
"""我的持仓：从手动交易流水 trades 聚合当前持仓与盈亏。

纯领域逻辑（只读/写 DuckDB，无第三方联网）。加权平均成本法：买入摊薄成本，
卖出按当时加权成本结转已实现盈亏、不改成本。最新价优先盘中快照、回退收盘。
"""
from __future__ import annotations

import pandas as pd

from ..data import store

_EPS = 1e-9


def record_trade(date: str, code: str, side: str, shares: float, price: float, note: str = "") -> int:
    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")
    cur = store.query("SELECT max(tid) m FROM trades") if store.has_table("trades") else pd.DataFrame()
    tid = int((cur["m"].iloc[0] if not cur.empty and pd.notna(cur["m"].iloc[0]) else 0)) + 1
    store.save("trades", pd.DataFrame([{
        "tid": tid, "date": date, "code": str(code), "side": side,
        "shares": float(shares), "price": float(price), "note": note}]))
    return tid


def list_trades() -> pd.DataFrame:
    if not store.has_table("trades"):
        return pd.DataFrame()
    return store.query("SELECT * FROM trades ORDER BY tid")


def delete_trade(tid: int) -> int:
    if not store.has_table("trades"):
        return 0
    with store.connect() as con:
        before = con.execute("SELECT count(*) FROM trades WHERE tid = ?", [tid]).fetchone()[0]
        con.execute("DELETE FROM trades WHERE tid = ?", [tid])
    return int(before)


def _latest_price(code: str) -> float | None:
    if store.has_table("quote_snapshot"):
        q = store.query(
            "SELECT close FROM quote_snapshot WHERE code = ? "
            "AND ts = (SELECT max(ts) FROM quote_snapshot WHERE code = ?)", [code, code])
        if not q.empty and pd.notna(q["close"].iloc[0]):
            return float(q["close"].iloc[0])
    d = store.load_daily(code)
    if not d.empty:
        return float(d["close"].iloc[-1])
    return None


def _name_of(code: str) -> str:
    if store.has_table("stock_basic"):
        r = store.query("SELECT name FROM stock_basic WHERE code = ?", [code])
        if not r.empty:
            return str(r["name"].iloc[0])
    return ""


def _positions() -> dict[str, dict]:
    """逐 code 按时间回放，得每只 {shares, avg_cost, realized}。"""
    df = list_trades()
    acc: dict[str, dict] = {}
    if df.empty:
        return acc
    for _, t in df.sort_values(["date", "tid"]).iterrows():
        p = acc.setdefault(t["code"], {"shares": 0.0, "avg_cost": 0.0, "realized": 0.0})
        sh, pr = float(t["shares"]), float(t["price"])
        if t["side"] == "buy":
            tot = p["shares"] + sh
            p["avg_cost"] = (p["shares"] * p["avg_cost"] + sh * pr) / tot if tot > _EPS else 0.0
            p["shares"] = tot
        else:  # sell
            p["realized"] += (pr - p["avg_cost"]) * sh
            p["shares"] -= sh
    return acc


def holdings() -> list[dict]:
    out = []
    for code, p in _positions().items():
        if p["shares"] <= _EPS:
            continue
        last = _latest_price(code)
        mv = (last or 0.0) * p["shares"]
        unreal = (last - p["avg_cost"]) * p["shares"] if last is not None else 0.0
        unreal_pct = (last / p["avg_cost"] - 1) * 100 if last is not None and p["avg_cost"] > _EPS else 0.0
        out.append({
            "code": code, "name": _name_of(code), "shares": round(p["shares"], 4),
            "avg_cost": round(p["avg_cost"], 4), "last_price": last,
            "market_value": round(mv, 2), "unrealized": round(unreal, 2),
            "unrealized_pct": round(unreal_pct, 2)})
    return out


def pnl_summary() -> dict:
    pos = _positions()
    realized = sum(p["realized"] for p in pos.values())
    unrealized = sum(h["unrealized"] for h in holdings())
    return {"realized": round(realized, 2), "unrealized": round(unrealized, 2),
            "total": round(realized + unrealized, 2)}
```

`aquant/portfolio/__init__.py`：空文件。

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_holdings.py -v`
Expected: PASS（2 tests）

- [ ] **Step 6: 提交**

```bash
git add aquant/portfolio aquant/data/store.py tests/test_holdings.py
git commit -m "feat(portfolio): trades 流水 + 持仓聚合与盈亏

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 卖出提醒（复用 decision 离线）

**Files:**
- Modify: `aquant/portfolio/holdings.py`（新增 `sell_alerts`、`holdings_view`）
- Test: `tests/test_holdings.py`（追加）

**Interfaces:**
- Consumes: `aquant.research.decision(code, offline=True) -> dict`（`battle_plan{stop_loss, take_profit}`、`signal`）；`holdings()`（Task 1）
- Produces:
  - `sell_alerts(code: str, last_price: float | None, dec: dict | None = None) -> list[str]`（标记集合：`"跌破止损"`/`"到压力位"`/`"信号转空"`；无触发返回空 list；`dec` 可注入便于测试，缺省取 `decision(code, offline=True)`）
  - `holdings_view() -> list[dict]`（= `holdings()` 每项追加 `alerts: list[str]`）

- [ ] **Step 1: 写失败测试（注入 dec，避免依赖真实因子）**

`tests/test_holdings.py` 追加：
```python
def test_sell_alerts_rules():
    from aquant.portfolio import holdings
    dec = {"battle_plan": {"stop_loss": 9.5, "take_profit": 12.0}, "signal": "持有/观望"}
    assert holdings.sell_alerts("600000", 9.4, dec=dec) == ["跌破止损"]
    assert holdings.sell_alerts("600000", 12.5, dec=dec) == ["到压力位"]
    assert holdings.sell_alerts("600000", 10.5, dec=dec) == []
    dec2 = {"battle_plan": {"stop_loss": 9.5, "take_profit": 12.0}, "signal": "回避/减持"}
    assert holdings.sell_alerts("600000", 10.5, dec=dec2) == ["信号转空"]


def test_holdings_view_attaches_alerts(seed_db, monkeypatch):
    from aquant.portfolio import holdings
    from aquant import research
    # 现价 13.95（fixture），构造止损在其上 → 触发跌破止损
    monkeypatch.setattr(research, "decision",
                        lambda code, offline=False: {"battle_plan": {"stop_loss": 14.0, "take_profit": 99.0}, "signal": "持有/观望"})
    holdings.record_trade("2026-02-02", "600000", "buy", 1000, 10.0)
    view = {h["code"]: h for h in holdings.holdings_view()}
    assert view["600000"]["alerts"] == ["跌破止损"]
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_holdings.py::test_sell_alerts_rules -v`
Expected: FAIL（`AttributeError: ... 'sell_alerts'`）

- [ ] **Step 3: 实现 `sell_alerts` + `holdings_view`**

在 `aquant/portfolio/holdings.py` 追加：
```python
def sell_alerts(code: str, last_price: float | None, dec: dict | None = None) -> list[str]:
    if last_price is None:
        return []
    if dec is None:
        from .. import research
        dec = research.decision(code, offline=True)
    if not dec:
        return []
    plan = dec.get("battle_plan", {})
    alerts = []
    stop, target = plan.get("stop_loss"), plan.get("take_profit")
    if stop is not None and last_price <= stop:
        alerts.append("跌破止损")
    if target is not None and last_price >= target:
        alerts.append("到压力位")
    if str(dec.get("signal", "")).startswith("回避"):
        alerts.append("信号转空")
    return alerts


def holdings_view() -> list[dict]:
    out = []
    for h in holdings():
        h = dict(h)
        h["alerts"] = sell_alerts(h["code"], h["last_price"])
        out.append(h)
    return out
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_holdings.py -v`
Expected: PASS（全部持仓用例）

- [ ] **Step 5: 提交**

```bash
git add aquant/portfolio/holdings.py tests/test_holdings.py
git commit -m "feat(portfolio): 卖出提醒 + holdings_view

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 持仓 API 端点

**Files:**
- Create: `server/schemas/holdings.py`, `server/routers/holdings.py`, `tests/test_holdings_api.py`
- Modify: `server/app.py`（include holdings router）

**Interfaces:**
- Consumes: `aquant.portfolio.holdings`（Task 1/2）
- Produces:
  - `POST /api/holdings/trade` body `TradeIn{date,code,side,shares,price,note?}` → `{tid}`
  - `GET /api/holdings/trades` → `TradesResp{rows: list[dict]}`
  - `DELETE /api/holdings/trade/{tid}` → `{deleted: int}`
  - `GET /api/holdings` → `HoldingsResp{rows: list[dict]}`（含 alerts）
  - `GET /api/holdings/pnl` → `PnlResp{realized, unrealized, total}`

- [ ] **Step 1: 写失败测试**

`tests/test_holdings_api.py`：
```python
def test_trade_crud_and_holdings(client, seed_db):
    # 记两笔买入
    r = client.post("/api/holdings/trade", json={"date": "2026-02-02", "code": "600000", "side": "buy", "shares": 1000, "price": 10.0})
    assert r.status_code == 200 and r.json()["tid"] == 1
    client.post("/api/holdings/trade", json={"date": "2026-02-03", "code": "600000", "side": "buy", "shares": 1000, "price": 12.0})
    # 持仓
    h = client.get("/api/holdings").json()["rows"]
    assert len(h) == 1 and h[0]["code"] == "600000" and h[0]["shares"] == 2000
    assert "alerts" in h[0]
    # 盈亏汇总
    pnl = client.get("/api/holdings/pnl").json()
    assert set(pnl) == {"realized", "unrealized", "total"}
    # 流水 + 删除
    assert len(client.get("/api/holdings/trades").json()["rows"]) == 2
    assert client.delete("/api/holdings/trade/1").json()["deleted"] == 1
    assert len(client.get("/api/holdings/trades").json()["rows"]) == 1
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_holdings_api.py -v`
Expected: FAIL（404）

- [ ] **Step 3: 写 schema**

`server/schemas/holdings.py`：
```python
from pydantic import BaseModel


class TradeIn(BaseModel):
    date: str
    code: str
    side: str
    shares: float
    price: float
    note: str = ""


class TradeCreated(BaseModel):
    tid: int


class TradesResp(BaseModel):
    rows: list[dict]


class HoldingsResp(BaseModel):
    rows: list[dict]


class PnlResp(BaseModel):
    realized: float
    unrealized: float
    total: float


class Deleted(BaseModel):
    deleted: int
```

- [ ] **Step 4: 写路由**

`server/routers/holdings.py`：
```python
from fastapi import APIRouter

from aquant.portfolio import holdings as h
from server.schemas.holdings import TradeIn, TradeCreated, TradesResp, HoldingsResp, PnlResp, Deleted

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.post("/trade", response_model=TradeCreated)
def add_trade(t: TradeIn) -> TradeCreated:
    tid = h.record_trade(t.date, t.code, t.side, t.shares, t.price, t.note)
    return TradeCreated(tid=tid)


@router.get("/trades", response_model=TradesResp)
def trades() -> TradesResp:
    df = h.list_trades()
    return TradesResp(rows=df.to_dict(orient="records") if not df.empty else [])


@router.delete("/trade/{tid}", response_model=Deleted)
def remove_trade(tid: int) -> Deleted:
    return Deleted(deleted=h.delete_trade(tid))


@router.get("", response_model=HoldingsResp)
def current() -> HoldingsResp:
    return HoldingsResp(rows=h.holdings_view())


@router.get("/pnl", response_model=PnlResp)
def pnl() -> PnlResp:
    return PnlResp(**h.pnl_summary())
```

- [ ] **Step 5: 注册路由**

`server/app.py` 的 routers import 行加入 `holdings`，并在其他 include 之后加 `app.include_router(holdings.router)`。

- [ ] **Step 6: 运行确认通过**

Run: `python3 -m pytest tests/test_holdings_api.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add server/schemas/holdings.py server/routers/holdings.py server/app.py tests/test_holdings_api.py
git commit -m "feat(holdings): 持仓/流水/盈亏 API 端点

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 复盘端点（briefing 离线 + 记分卡结构化）

**Files:**
- Modify: `aquant/research.py`（`briefing` 加 `offline` 参数并透传）
- Create: `server/schemas/assist.py`, `server/routers/assist.py`, `tests/test_assist_api.py`
- Modify: `server/app.py`（include assist router）

**Interfaces:**
- Consumes: `aquant.research.briefing(top, offline=True)`；`aquant.track.evaluate.forward_returns()`
- Produces:
  - `GET /api/assist/briefing?top=N` → `BriefingResp{rows: list[dict]}`（briefing 表转 records；调用 `briefing(top=N, offline=True)`）
  - `GET /api/assist/scorecard` → `ScorecardResp{as_of: str | null, rows: list[dict]}`（`forward_returns()` 转 records；空台账时 `rows=[]`）

- [ ] **Step 1: 给 briefing 加 offline 参数**

修改 `aquant/research.py` 的 `briefing` 签名与内部调用：
- 签名改为：`def briefing(top: int = 12, weights: dict | None = None, offline: bool = False) -> pd.DataFrame:`
- 把循环内 `rep = stock_report(code, market_scores=ms)` 改为 `rep = stock_report(code, market_scores=ms, offline=offline)`
- 把 `d = decision(code, rep=rep)` 改为 `d = decision(code, rep=rep, offline=offline)`

- [ ] **Step 2: 写失败测试（mock 领域函数，避免真实全市场打分/联网）**

`tests/test_assist_api.py`：
```python
import pandas as pd


def test_briefing_endpoint_offline(client, monkeypatch):
    import aquant.research as research
    called = {}
    def fake_briefing(top=12, weights=None, offline=False):
        called["offline"] = offline
        return pd.DataFrame([{"code": "600000", "name": "浦发", "综合分": 1.2, "信号": "买入/增持"}])
    monkeypatch.setattr(research, "briefing", fake_briefing)
    r = client.get("/api/assist/briefing?top=5")
    assert r.status_code == 200
    assert r.json()["rows"][0]["code"] == "600000"
    assert called["offline"] is True  # 端点必须以离线调用，守住不联网铁律


def test_scorecard_endpoint(client, monkeypatch):
    from aquant.track import evaluate
    monkeypatch.setattr(evaluate, "forward_returns",
                        lambda: pd.DataFrame([{"as_of": "2026-06-01", "code": "600000", "rank": 1, "fwd_20": 0.03, "exc_20": 0.01}]))
    r = client.get("/api/assist/scorecard")
    assert r.status_code == 200
    body = r.json()
    assert body["as_of"] == "2026-06-01"
    assert body["rows"][0]["exc_20"] == 0.01


def test_scorecard_empty(client, monkeypatch):
    from aquant.track import evaluate
    monkeypatch.setattr(evaluate, "forward_returns", lambda: pd.DataFrame())
    r = client.get("/api/assist/scorecard")
    assert r.status_code == 200
    assert r.json() == {"as_of": None, "rows": []}
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_assist_api.py -v`
Expected: FAIL（404）

- [ ] **Step 4: 写 schema + 路由**

`server/schemas/assist.py`：
```python
from pydantic import BaseModel


class BriefingResp(BaseModel):
    rows: list[dict]


class ScorecardResp(BaseModel):
    as_of: str | None
    rows: list[dict]
```

`server/routers/assist.py`：
```python
from fastapi import APIRouter

from aquant import research
from aquant.track import evaluate
from server.schemas.assist import BriefingResp, ScorecardResp

router = APIRouter(prefix="/api/assist", tags=["assist"])


@router.get("/briefing", response_model=BriefingResp)
def briefing(top: int = 12) -> BriefingResp:
    df = research.briefing(top=top, offline=True)
    return BriefingResp(rows=df.to_dict(orient="records") if not df.empty else [])


@router.get("/scorecard", response_model=ScorecardResp)
def scorecard() -> ScorecardResp:
    df = evaluate.forward_returns()
    if df.empty:
        return ScorecardResp(as_of=None, rows=[])
    as_of = str(df["as_of"].iloc[0]) if "as_of" in df.columns else None
    return ScorecardResp(as_of=as_of, rows=df.to_dict(orient="records"))
```

- [ ] **Step 5: 注册路由**

`server/app.py` 的 routers import 行加入 `assist`，并加 `app.include_router(assist.router)`。

- [ ] **Step 6: 运行确认通过 + 全量回归**

Run: `python3 -m pytest tests/test_assist_api.py -v && python3 -m pytest -q`
Expected: assist 3 用例 PASS；全套（1A 18 + 持仓/assist 新增）全绿。

- [ ] **Step 7: 提交**

```bash
git add aquant/research.py server/schemas/assist.py server/routers/assist.py server/app.py tests/test_assist_api.py
git commit -m "feat(assist): 复盘端点 briefing(离线)/scorecard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照 Phase 2 设计第 1 节后端）：
- trades 表 + CRUD → Task 1/3。✅
- 持仓聚合 + 加权成本 + 浮动盈亏 + 已实现盈亏 → Task 1。✅
- 卖出提醒（跌破止损/到压力/信号转空，复用 decision 离线）→ Task 2。✅
- holdings/pnl/trades 端点 → Task 3。✅
- 复盘记分卡（forward_returns 结构化）+ 研报速览（briefing 离线）→ Task 4。✅
- 铁律不联网：briefing/decision 均以 offline=True 调用（Task 2/4）；写仅 trades（Task 3）。✅

**占位符扫描**：无 TBD/TODO；每步含完整可运行代码。✅

**类型一致性**：`record_trade/list_trades/delete_trade/holdings/holdings_view/sell_alerts/pnl_summary/_latest_price` 在领域层与路由层引用一致；端点 `response_model` 与 schema 字段（TradeIn/TradeCreated/TradesResp/HoldingsResp/PnlResp/Deleted/BriefingResp/ScorecardResp）一致；`briefing(offline=)` 新签名在 Task 1 调用方与 Task 4 端点一致。✅

**范围**：单一可测后端子系统（pytest 全绿）。前端为独立 Plan 2B。✅

**已知风险**：`delete_trade` 用 `store.connect()` 直接执行 DELETE（store 现有读路径为 query；此处需要 DDL/DML 执行）——实现时确认 `store.connect()` 上下文管理器可执行 `con.execute(DELETE)` 并自动提交（DuckDB 默认 autocommit）。若 store 未暴露 connect，改用 store 内等价写法或新增最小 helper。
