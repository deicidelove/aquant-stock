# v3A — 自选股看板后端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 后端支撑「自选股看板」：watchlist 表 + 自选 CRUD + 看板服务（自选∪持仓，每只即时算出信号/关键价位/迷你K线/提醒）+ 端点，全部只读库（仅 watchlist 写），请求内不联网。

**Architecture:** 新增 `watchlist` 表；`aquant/portfolio/watchlist.py` 领域层复用 `research.decision(offline=True)`（信号/价位/风险）、`portfolio.holdings`（持仓码/`sell_alerts`/`_latest_price`/`_name_of`）、`store.load_daily`（迷你K线）；FastAPI `/api/watchlist` + `/api/board` 薄封装。

**Tech Stack:** Python 3.11 · FastAPI · DuckDB(`aquant.data.store`) · pytest + httpx TestClient。

## Global Constraints

- Python 3.11；复用现有领域核心；新增看板逻辑放 `aquant/portfolio/watchlist.py`。
- DB 路径由 `AQUANT_DATA_DIR` 驱动；测试在 import 任何 aquant 前设置（沿用 `tests/conftest.py`）。
- 新表在 `store.TABLE_KEYS` 注册主键。
- API 请求处理内**禁止**第三方网络；只允许 `store` 读写 + 复用领域函数（`decision` 以 `offline=True` 调用）。写操作仅限 `watchlist` 表。
- 端点路径以 `/api` 前缀；pydantic 响应模型。
- 本期看板**不含 news**（延后）；缺历史的票 decision 返回空时，卡片相应字段留空/默认，不报错。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `v3a-backend` 上开发；每 Task 末尾提交。
- 复用契约（已核对）：
  - `aquant.research.decision(code, rep=None, offline=False) -> dict`：含 `signal`、`one_liner`、`battle_plan{ideal_buy,secondary_buy,stop_loss,take_profit,position}`、`risk_level`；历史不足时返回 `{}`。
  - `aquant.portfolio.holdings`：`sell_alerts(code, last_price, dec=None) -> list[str]`、`_latest_price(code) -> float|None`（quote_snapshot→daily_bar 回退）、`_name_of(code) -> str`、`_positions() -> dict[code,{shares,...}]`。
  - `aquant.data.store.save/query/has_table/connect/load_daily`。

---

### Task 1: watchlist 表 + 自选 CRUD + 端点

**Files:**
- Create: `aquant/portfolio/watchlist.py`, `server/schemas/watchlist.py`, `server/routers/watchlist.py`, `tests/test_watchlist.py`
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `watchlist`）, `server/app.py`（include watchlist router）, `tests/conftest.py`（seed_db 隔离清理加 watchlist）

**Interfaces:**
- Produces：
  - `aquant.portfolio.watchlist.add(code: str) -> None`（写一行；已存在则幂等）
  - `remove(code: str) -> int`（删除，返回删除行数）
  - `list_codes() -> list[str]`（自选码，按加入时间升序）
  - `POST /api/watchlist {code}` → `{codes: [...]}`（加后返回全量）
  - `DELETE /api/watchlist/{code}` → `{codes: [...]}`
  - `GET /api/watchlist` → `{codes: [...]}`

- [ ] **Step 1: 注册表主键**

`aquant/data/store.py` 的 `TABLE_KEYS` 新增：
```python
    "watchlist": ["code"],
```

`tests/conftest.py` 的 `seed_db` fixture 里，与既有 `DROP TABLE IF EXISTS fund_flow`/`sector_fund_flow` 同处，追加一行清理（临时库跨测试共享，保证自选隔离）：
```python
        con.execute("DROP TABLE IF EXISTS watchlist")
```

- [ ] **Step 2: 写失败测试**

`tests/test_watchlist.py`：
```python
def test_add_list_remove(seed_db):
    from aquant.portfolio import watchlist
    watchlist.add("600000")
    watchlist.add("000001")
    watchlist.add("600000")  # 幂等
    assert watchlist.list_codes() == ["600000", "000001"]
    assert watchlist.remove("600000") == 1
    assert watchlist.list_codes() == ["000001"]


def test_watchlist_api(client, seed_db):
    assert client.get("/api/watchlist").json()["codes"] == []
    r = client.post("/api/watchlist", json={"code": "600000"})
    assert r.status_code == 200 and r.json()["codes"] == ["600000"]
    client.post("/api/watchlist", json={"code": "000001"})
    assert client.delete("/api/watchlist/600000").json()["codes"] == ["000001"]
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_watchlist.py -v`
Expected: FAIL（`ModuleNotFoundError: aquant.portfolio.watchlist` / 404）

- [ ] **Step 4: 实现 watchlist.py**

`aquant/portfolio/watchlist.py`：
```python
"""自选股：增删查（watchlist 表）。看板 board() 见后续任务。"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..data import store


def add(code: str) -> None:
    store.save("watchlist", pd.DataFrame([{
        "code": str(code), "added_ts": datetime.now().isoformat(timespec="seconds")}]))


def remove(code: str) -> int:
    if not store.has_table("watchlist"):
        return 0
    with store.connect() as con:
        before = con.execute("SELECT count(*) FROM watchlist WHERE code = ?", [code]).fetchone()[0]
        con.execute("DELETE FROM watchlist WHERE code = ?", [code])
    return int(before)


def list_codes() -> list[str]:
    if not store.has_table("watchlist"):
        return []
    df = store.query("SELECT code FROM watchlist ORDER BY added_ts, code")
    return [str(c) for c in df["code"].tolist()]
```

- [ ] **Step 5: 写 schema + 路由 + 注册**

`server/schemas/watchlist.py`：
```python
from pydantic import BaseModel


class CodeIn(BaseModel):
    code: str


class Codes(BaseModel):
    codes: list[str]
```

`server/routers/watchlist.py`：
```python
from fastapi import APIRouter

from aquant.portfolio import watchlist
from server.schemas.watchlist import CodeIn, Codes

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("", response_model=Codes)
def get_watchlist() -> Codes:
    return Codes(codes=watchlist.list_codes())


@router.post("", response_model=Codes)
def add_watchlist(body: CodeIn) -> Codes:
    watchlist.add(body.code)
    return Codes(codes=watchlist.list_codes())


@router.delete("/{code}", response_model=Codes)
def remove_watchlist(code: str) -> Codes:
    watchlist.remove(code)
    return Codes(codes=watchlist.list_codes())
```

`server/app.py`：routers import 行加 `watchlist`，并加 `app.include_router(watchlist.router)`。

- [ ] **Step 6: 运行确认通过**

Run: `python3 -m pytest tests/test_watchlist.py -v`
Expected: PASS（2 tests）

- [ ] **Step 7: 提交**

```bash
git add aquant/portfolio/watchlist.py aquant/data/store.py server/schemas/watchlist.py server/routers/watchlist.py tests/test_watchlist.py server/app.py
git commit -m "feat(watchlist): 自选表 + 增删查 + 端点

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 看板服务 board() + /api/board 端点

**Files:**
- Modify: `aquant/portfolio/watchlist.py`（新增 `board`）, `server/schemas/watchlist.py`（`BoardResp`）, `server/routers/watchlist.py`（`/api/board`）
- Test: `tests/test_watchlist.py`（追加）

**Interfaces:**
- Consumes: `watchlist.list_codes`；`holdings._positions`/`sell_alerts`/`_latest_price`/`_name_of`；`research.decision(offline=True)`；`store.load_daily`
- Produces：
  - `aquant.portfolio.watchlist.board(kline_n: int = 30) -> list[dict]`：对 **自选 ∪ 持仓(shares>0)** 去重的每只 code，返回卡片：
    `{code, name, last_price, pct_chg, kline:[{date,close}], signal, one_liner, battle_plan, risk_level, alerts}`。
    - `last_price` = `holdings._latest_price(code)`；`pct_chg` = `daily_bar` 最新行 pct_chg（无则 None）
    - `kline` = `load_daily(code)` 尾 `kline_n` 行的 `{date,close}`
    - `dec = research.decision(code, offline=True)`；`signal/one_liner/battle_plan/risk_level` 取自 dec（dec 为空则分别为 ""/""/{}/""）
    - `alerts = holdings.sell_alerts(code, last_price, dec=dec)`
    - 历史不足（`load_daily` 空）的 code 跳过
  - `GET /api/board` → `BoardResp{rows: list[dict]}`

- [ ] **Step 1: 写失败测试**

`tests/test_watchlist.py` 追加：
```python
def test_board_union_and_card(seed_db):
    from aquant.portfolio import watchlist, holdings
    watchlist.add("600000")                       # 自选
    holdings.record_trade("2026-02-02", "000001", "buy", 1000, 20.0)  # 持仓
    rows = {r["code"]: r for r in watchlist.board(kline_n=10)}
    assert set(rows) == {"600000", "000001"}      # 自选 ∪ 持仓
    c = rows["600000"]
    assert c["name"] == "浦发银行"
    assert c["last_price"] is not None
    assert len(c["kline"]) == 10 and set(c["kline"][0]) == {"date", "close"}
    assert "signal" in c and isinstance(c["alerts"], list)
    assert set(["ideal_buy", "stop_loss", "take_profit"]).issubset(c["battle_plan"]) or c["battle_plan"] == {}


def test_board_api(client, seed_db):
    from aquant.portfolio import watchlist
    watchlist.add("600000")
    r = client.get("/api/board")
    assert r.status_code == 200
    assert r.json()["rows"][0]["code"] == "600000"
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_watchlist.py::test_board_union_and_card -v`
Expected: FAIL（`AttributeError: ...'board'`）

- [ ] **Step 3: 实现 board()**

`aquant/portfolio/watchlist.py` 追加（顶部加 `from .. import research`、`from . import holdings`）：
```python
def board(kline_n: int = 30) -> list[dict]:
    held = {c for c, p in holdings._positions().items() if p["shares"] > 1e-9}
    codes = list(dict.fromkeys(list_codes() + sorted(held)))  # 自选在前，持仓补齐，去重
    out = []
    for code in codes:
        df = store.load_daily(code)
        if df.empty:
            continue
        last_row = df.iloc[-1]
        last_price = holdings._latest_price(code)
        pct_chg = float(last_row["pct_chg"]) if "pct_chg" in df.columns and pd.notna(last_row["pct_chg"]) else None
        kline = [{"date": str(r["date"]), "close": float(r["close"])}
                 for _, r in df.tail(kline_n).iterrows()]
        dec = research.decision(code, offline=True) or {}
        out.append({
            "code": code, "name": holdings._name_of(code),
            "last_price": last_price, "pct_chg": pct_chg, "kline": kline,
            "signal": dec.get("signal", ""), "one_liner": dec.get("one_liner", ""),
            "battle_plan": dec.get("battle_plan", {}), "risk_level": dec.get("risk_level", ""),
            "alerts": holdings.sell_alerts(code, last_price, dec=dec or None),
        })
    return out
```

- [ ] **Step 4: 加 schema + 路由**

`server/schemas/watchlist.py` 追加：
```python
class BoardResp(BaseModel):
    rows: list[dict]
```

`server/routers/watchlist.py` 追加（顶部 import 补 `BoardResp`；新增独立路由，注意 board 不在 `/api/watchlist` 前缀下）：
```python
from fastapi import APIRouter as _AR  # 复用已 import 的 APIRouter 亦可
from server.schemas.watchlist import BoardResp

board_router = APIRouter(prefix="/api", tags=["board"])


@board_router.get("/board", response_model=BoardResp)
def get_board() -> BoardResp:
    return BoardResp(rows=watchlist.board())
```
（实现时：直接在文件内再建一个 `board_router = APIRouter(prefix="/api")` 并定义 `/board`；`server/app.py` 里 `from server.routers import watchlist` 后 `app.include_router(watchlist.board_router)`。避免把 `/board` 挂到 `/api/watchlist` 前缀下。）

`server/app.py`：在 `app.include_router(watchlist.router)` 后加 `app.include_router(watchlist.board_router)`。

- [ ] **Step 5: 运行确认通过 + 全量回归**

Run: `python3 -m pytest tests/test_watchlist.py -v && python3 -m pytest -q`
Expected: watchlist 全部 PASS；全套全绿。

- [ ] **Step 6: 提交**

```bash
git add aquant/portfolio/watchlist.py server/schemas/watchlist.py server/routers/watchlist.py server/app.py tests/test_watchlist.py
git commit -m "feat(watchlist): 看板 board(自选∪持仓卡片) + /api/board

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照 v3 第 1 节后端）：
- watchlist 表 + add/remove/list + 端点 → Task 1。✅
- 看板 board（自选∪持仓，卡片=行情/迷你K线/信号/关键价位/风险/提醒）→ Task 2。✅
- 数据即时算自 daily_bar（decision/kline），不依赖未灌快照 → Task 2 用 `load_daily`+`decision(offline)`。✅
- 本期不含 news（延后）→ 卡片无 news 字段。✅
- 铁律：端点只读库+复用领域（decision offline 不联网）；写仅 watchlist。✅

**占位符扫描**：无 TBD/TODO；每步含完整代码。✅

**类型一致性**：`add/remove/list_codes/board` 领域层与路由一致；`board` 卡片字段与 Plan B 前端将消费的结构一致（code/name/last_price/pct_chg/kline/signal/one_liner/battle_plan/risk_level/alerts）；schema（CodeIn/Codes/BoardResp）与端点 response_model 一致；复用 `holdings._positions/_latest_price/_name_of/sell_alerts`、`research.decision` 签名匹配。✅

**范围**：单一可测后端子系统（pytest 全绿）。前端为独立 Plan B。✅

**已知前提**：
- `decision(offline=True)` 对每只 board code 现算（含 score_fast(universe)）——自选/持仓数量少，耗时可接受；若将来自选很多可加物化/缓存（本期 YAGNI）。
- board 复用 holdings 私有函数（`_positions/_latest_price/_name_of`）——同 `aquant.portfolio` 包内，可接受；如需可后续提为公有。
- 测试 `test_watchlist.py` 会写 watchlist/trades；conftest 已对 trades 做隔离，watchlist 需在测试内 remove 或依赖 seed 顺序——测试用例自洽（add 后即断言，跨用例用不同 code / 幂等）。若出现跨用例污染，在 conftest seed_db 增补 `DROP TABLE IF EXISTS watchlist`（与 trades/fund_flow 同处）。
