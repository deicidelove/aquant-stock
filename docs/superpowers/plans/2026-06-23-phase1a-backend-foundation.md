# Phase 1A — 后端地基 + 驾驶舱 API 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立"后台刷新层 + 物化评分 + FastAPI 只读库出 JSON"的后端地基，并交付驾驶舱所需的全部 API 端点。

**Architecture:** 第三方数据只由后台刷新层（APScheduler 定时任务）落 DuckDB；FastAPI 端点只读 DuckDB 与复用 `aquant/` 领域函数，绝不在请求内联网。物化 `factor_score` 表把全市场打分从 30–60s 降到查表 ms 级。

**Tech Stack:** Python 3.11 · FastAPI · uvicorn · APScheduler · DuckDB（复用 `aquant.data.store`）· pytest + httpx TestClient。

## Global Constraints

- Python 3.11；复用现有 `aquant/` 领域核心，不重写策略/回测逻辑。
- 数据库路径由环境变量 `AQUANT_DATA_DIR` 驱动（`aquant.config.DB_PATH = $AQUANT_DATA_DIR/market.duckdb`）；测试必须在 import 任何 `aquant` 模块**之前**设置该环境变量指向临时目录。
- 新建表必须在 `aquant/data/store.py` 的 `TABLE_KEYS` 注册主键（`save()` 用其做幂等 upsert）。
- API 端点请求处理内**禁止**任何第三方网络调用；只允许 `store.query` / `store.load_daily` / 复用领域函数（这些函数在被 API 调用时只读库）。
- 所有端点路径以 `/api` 前缀；JSON 响应用 pydantic 模型声明。
- 测试用 `httpx` + FastAPI `TestClient`，针对 conftest 注入的临时 DuckDB（含最小 fixture 数据），不依赖真实行情库、不联网。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 项目当前非 git 仓库；**Task 1 第一步先 `git init`**，之后每个 Task 末尾提交。

---

### Task 1: 项目骨架 + 依赖 + 健康检查端点

**Files:**
- Create: `server/__init__.py`, `server/app.py`, `server/routers/__init__.py`, `server/routers/health.py`
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/test_health.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces:
  - `server.app.create_app(start_scheduler: bool = True) -> fastapi.FastAPI`
  - `GET /api/health` → `{"status": "ok", "db": bool, "latest_bar_date": str | None}`
  - pytest fixture `client` (FastAPI TestClient, scheduler 关闭, 临时 DB 已 seed)
  - pytest fixture `seed_db()` — 在临时 DB 写入最小 `daily_bar` + `stock_basic`

- [ ] **Step 1: git init + 追加依赖**

```bash
cd /Volumes/demon/code/ml/study/stock
git init
printf '\n# v2 backend\nfastapi>=0.110\nuvicorn[standard]>=0.29\nAPScheduler>=3.10\nhttpx>=0.27\npytest>=8.0\n' >> requirements.txt
python3 -m pip install "fastapi>=0.110" "uvicorn[standard]>=0.29" "APScheduler>=3.10" "httpx>=0.27" "pytest>=8.0"
```

- [ ] **Step 2: 写 conftest（临时 DB + fixtures）**

`tests/conftest.py`：
```python
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# 必须在 import 任何 aquant 模块之前设置数据目录
_TMP = tempfile.mkdtemp(prefix="aquant_test_")
os.environ["AQUANT_DATA_DIR"] = _TMP


@pytest.fixture()
def seed_db():
    """向临时 DuckDB 写入最小行情数据：2 只股票、各 80 个交易日。"""
    from aquant.data import store
    dates = pd.bdate_range("2026-01-01", periods=80).strftime("%Y-%m-%d").tolist()
    rows = []
    for code, base in (("600000", 10.0), ("000001", 20.0)):
        for i, d in enumerate(dates):
            px = base + i * 0.05
            rows.append({"code": code, "date": d, "open": px, "high": px * 1.02,
                         "low": px * 0.98, "close": px, "volume": 1e6 + i,
                         "amount": px * 1e6, "turnover": 1.5, "pct_chg": 0.5})
    store.save("daily_bar", pd.DataFrame(rows))
    store.save("stock_basic", pd.DataFrame(
        [{"code": "600000", "name": "浦发银行", "market": "sh"},
         {"code": "000001", "name": "平安银行", "market": "sz"}]))
    return store


@pytest.fixture()
def client(seed_db):
    from fastapi.testclient import TestClient
    from server.app import create_app
    return TestClient(create_app(start_scheduler=False))
```

- [ ] **Step 3: 写失败测试**

`tests/test_health.py`：
```python
def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["latest_bar_date"] == "2026-04-21"  # 80 个工作日后的最后一日
```

- [ ] **Step 4: 运行测试确认失败**

Run: `python3 -m pytest tests/test_health.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server'`）

- [ ] **Step 5: 实现 health 路由**

`server/routers/health.py`：
```python
from fastapi import APIRouter

from aquant.data import store

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict:
    has = store.has_table("daily_bar")
    latest = store.max_date("daily_bar") if has else None
    return {"status": "ok", "db": has, "latest_bar_date": latest}
```

- [ ] **Step 6: 实现 app 工厂**

`server/app.py`：
```python
from fastapi import FastAPI

from server.routers import health


def create_app(start_scheduler: bool = True) -> FastAPI:
    app = FastAPI(title="Aquant API", version="2.0")
    app.include_router(health.router)
    # 调度器在 Task 6 接入；此处保留参数占位
    app.state.start_scheduler = start_scheduler
    return app
```

`server/__init__.py` 与 `server/routers/__init__.py`：空文件。
`tests/__init__.py`：空文件。

- [ ] **Step 7: 运行测试确认通过**

Run: `python3 -m pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add server tests requirements.txt
git commit -m "feat(server): FastAPI 骨架 + /api/health 健康检查

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 实时快照数据源 `spot_snapshot()`

**Files:**
- Modify: `aquant/data/sources/akshare_source.py`（在 `index_daily` 之后新增函数）
- Test: `tests/test_spot_snapshot.py`

**Interfaces:**
- Produces: `aquant.data.sources.akshare_source.spot_snapshot() -> pd.DataFrame`，列固定为 `[code, name, close, pct_chg, turnover, amount]`（code 6 位补零字符串）。

- [ ] **Step 1: 写失败测试（mock akshare）**

`tests/test_spot_snapshot.py`：
```python
import pandas as pd


def test_spot_snapshot_normalizes(monkeypatch):
    from aquant.data.sources import akshare_source as src
    raw = pd.DataFrame({
        "代码": ["600000", "1"], "名称": ["浦发", "平安"],
        "最新价": [10.1, 20.2], "涨跌幅": [1.2, -0.5],
        "换手率": [1.5, 2.0], "成交额": [1e8, 2e8],
    })
    monkeypatch.setattr(src.ak, "stock_zh_a_spot_em", lambda: raw)
    df = src.spot_snapshot()
    assert list(df.columns) == ["code", "name", "close", "pct_chg", "turnover", "amount"]
    assert df["code"].tolist() == ["600000", "000001"]  # 补零
    assert df.loc[df["code"] == "600000", "close"].iloc[0] == 10.1
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_spot_snapshot.py -v`
Expected: FAIL（`AttributeError: module ... has no attribute 'spot_snapshot'`）

- [ ] **Step 3: 实现 `spot_snapshot`**

在 `aquant/data/sources/akshare_source.py` 的 `index_daily` 函数之后追加：
```python
_SPOT_MAP = {"代码": "code", "名称": "name", "最新价": "close",
             "涨跌幅": "pct_chg", "换手率": "turnover", "成交额": "amount"}


@_robust
def spot_snapshot() -> pd.DataFrame:
    """全市场现价快照（盘中分钟级）。columns=[code,name,close,pct_chg,turnover,amount]。"""
    df = ak.stock_zh_a_spot_em().rename(columns=_SPOT_MAP)
    df["code"] = df["code"].astype(str).str.zfill(6)
    keep = list(_SPOT_MAP.values())
    return df[[c for c in keep if c in df.columns]].copy()
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_spot_snapshot.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add aquant/data/sources/akshare_source.py tests/test_spot_snapshot.py
git commit -m "feat(source): 新增 spot_snapshot 全市场现价快照

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 盘中现价快照入库 `refresh_quotes()`

**Files:**
- Create: `server/refresh/__init__.py`, `server/refresh/snapshots.py`
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `quote_snapshot`）
- Test: `tests/test_snapshots.py`

**Interfaces:**
- Consumes: `akshare_source.spot_snapshot()`（Task 2）
- Produces: `server.refresh.snapshots.refresh_quotes(fetch=None) -> int`（写 `quote_snapshot` 表，列 `[code,name,close,pct_chg,turnover,amount,ts]`，返回写入行数；`fetch` 可注入替身便于测试）

- [ ] **Step 1: 注册表主键**

`aquant/data/store.py` 的 `TABLE_KEYS` 字典内新增一行：
```python
    "quote_snapshot": ["code", "ts"],
```

- [ ] **Step 2: 写失败测试**

`tests/test_snapshots.py`：
```python
import pandas as pd


def test_refresh_quotes_writes_rows(seed_db):
    from server.refresh import snapshots
    fake = pd.DataFrame({
        "code": ["600000", "000001"], "name": ["浦发", "平安"],
        "close": [10.1, 20.2], "pct_chg": [1.2, -0.5],
        "turnover": [1.5, 2.0], "amount": [1e8, 2e8],
    })
    n = snapshots.refresh_quotes(fetch=lambda: fake)
    assert n == 2
    rows = seed_db.query("SELECT code, close, ts FROM quote_snapshot ORDER BY code")
    assert set(rows["code"]) == {"000001", "600000"}
    assert rows["ts"].notna().all()
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_snapshots.py::test_refresh_quotes_writes_rows -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server.refresh'`）

- [ ] **Step 4: 实现 `refresh_quotes`**

`server/refresh/snapshots.py`：
```python
"""盘中快照刷新任务：拉第三方现价/板块/指数 → 落 DuckDB。只在后台运行。"""
from __future__ import annotations

from datetime import datetime

from aquant.data import store
from aquant.data.sources import akshare_source as src


def refresh_quotes(fetch=None) -> int:
    """全市场现价快照入库 quote_snapshot，返回写入行数。"""
    fetch = fetch or src.spot_snapshot
    df = fetch()
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["ts"] = datetime.now().isoformat(timespec="seconds")
    return store.save("quote_snapshot", df)
```

`server/refresh/__init__.py`：空文件。

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_snapshots.py::test_refresh_quotes_writes_rows -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add server/refresh aquant/data/store.py tests/test_snapshots.py
git commit -m "feat(refresh): 盘中现价快照入库 refresh_quotes

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 板块快照入库 `refresh_sectors()`

**Files:**
- Modify: `server/refresh/snapshots.py`（新增函数）
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `sector_snapshot`）
- Test: `tests/test_snapshots.py`（追加用例）

**Interfaces:**
- Consumes: `akshare_source.industry_snapshot() -> pd.DataFrame`（现有，含列 `sector`/`pct_chg`/`mkt_cap` 等）
- Produces: `server.refresh.snapshots.refresh_sectors(fetch=None) -> int`（写 `sector_snapshot`，在源列基础上加 `ts`）

- [ ] **Step 1: 注册表主键**

`aquant/data/store.py` 的 `TABLE_KEYS` 新增：
```python
    "sector_snapshot": ["sector", "ts"],
```

- [ ] **Step 2: 写失败测试（追加到 tests/test_snapshots.py）**

```python
def test_refresh_sectors_writes_rows(seed_db):
    from server.refresh import snapshots
    fake = pd.DataFrame({"sector": ["银行", "煤炭"], "pct_chg": [1.1, -0.3],
                         "mkt_cap": [5e11, 2e11]})
    n = snapshots.refresh_sectors(fetch=lambda: fake)
    assert n == 2
    rows = seed_db.query("SELECT sector, ts FROM sector_snapshot ORDER BY sector")
    assert set(rows["sector"]) == {"银行", "煤炭"}
    assert rows["ts"].notna().all()
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_snapshots.py::test_refresh_sectors_writes_rows -v`
Expected: FAIL（`AttributeError: ... 'refresh_sectors'`）

- [ ] **Step 4: 实现 `refresh_sectors`**

在 `server/refresh/snapshots.py` 追加：
```python
def refresh_sectors(fetch=None) -> int:
    """行业板块快照入库 sector_snapshot，返回写入行数。"""
    fetch = fetch or src.industry_snapshot
    df = fetch()
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["ts"] = datetime.now().isoformat(timespec="seconds")
    return store.save("sector_snapshot", df)
```

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_snapshots.py -v`
Expected: PASS（两个快照用例均通过）

- [ ] **Step 6: 提交**

```bash
git add server/refresh/snapshots.py aquant/data/store.py tests/test_snapshots.py
git commit -m "feat(refresh): 板块快照入库 refresh_sectors

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 物化因子评分表 `materialize_scores()` + 读取

**Files:**
- Create: `server/refresh/scores.py`
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `factor_score`）
- Test: `tests/test_scores.py`

**Interfaces:**
- Consumes: `aquant.select.scorer.score_fast(codes=None, weights=None, top=int) -> pd.DataFrame[code,name,score]`；`aquant.research.universe() -> list[str]`
- Produces:
  - `server.refresh.scores.materialize_scores(top: int = 10000) -> int`（计算全市场综合分写 `factor_score`，列 `[code,name,score,as_of]`，`as_of` = `daily_bar` 最新日期；返回行数）
  - `server.refresh.scores.read_top_scores(top: int = 50) -> pd.DataFrame`（读最新 `as_of` 的前 `top` 行，按 score 降序）

- [ ] **Step 1: 注册表主键**

`aquant/data/store.py` 的 `TABLE_KEYS` 新增：
```python
    "factor_score": ["code", "as_of"],
```

- [ ] **Step 2: 写失败测试**

`tests/test_scores.py`：
```python
def test_materialize_then_read(seed_db):
    from server.refresh import scores
    n = scores.materialize_scores()
    assert n >= 2  # 至少 2 只 fixture 股票被打分
    top = scores.read_top_scores(top=1)
    assert len(top) == 1
    assert set(["code", "name", "score", "as_of"]).issubset(top.columns)
    assert top["as_of"].iloc[0] == "2026-04-21"  # daily_bar 最新日
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_scores.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server.refresh.scores'`）

- [ ] **Step 4: 实现 `scores.py`**

`server/refresh/scores.py`：
```python
"""物化全市场因子综合分：收盘后批量计算落 factor_score，API 查表替代每次现算。"""
from __future__ import annotations

from aquant.data import store
from aquant.select import scorer
from aquant import research


def materialize_scores(top: int = 10000) -> int:
    """计算全市场综合分写 factor_score（as_of=daily_bar 最新日），返回写入行数。"""
    as_of = store.max_date("daily_bar")
    if as_of is None:
        return 0
    ranked = scorer.score_fast(codes=research.universe(), top=top)
    if ranked.empty:
        return 0
    ranked = ranked.copy()
    ranked["as_of"] = as_of
    cols = [c for c in ("code", "name", "score", "as_of") if c in ranked.columns]
    return store.save("factor_score", ranked[cols])


def read_top_scores(top: int = 50):
    """读最新 as_of 的前 top 名（按 score 降序）。"""
    if not store.has_table("factor_score"):
        import pandas as pd
        return pd.DataFrame()
    return store.query(
        "SELECT code, name, score, as_of FROM factor_score "
        "WHERE as_of = (SELECT max(as_of) FROM factor_score) "
        "ORDER BY score DESC LIMIT ?", [top])
```

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_scores.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add server/refresh/scores.py aquant/data/store.py tests/test_scores.py
git commit -m "feat(refresh): 物化因子评分表 materialize/read

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: 交易时段门控 + APScheduler 接入生命周期

**Files:**
- Create: `server/refresh/scheduler.py`
- Modify: `server/app.py`（lifespan 启停调度器）
- Test: `tests/test_scheduler.py`

**Interfaces:**
- Consumes: `refresh_quotes`/`refresh_sectors`（Task 3/4）、`materialize_scores`（Task 5）
- Produces:
  - `server.refresh.scheduler.is_trading_hours(now: datetime) -> bool`（周一至周五 09:30–11:30 或 13:00–15:00 为 True）
  - `server.refresh.scheduler.build_scheduler() -> BackgroundScheduler`（注册盘中快照 job 每 2min + 收盘后物化 job 15:30；不自动 start）

- [ ] **Step 1: 写失败测试（纯逻辑，不起真实定时）**

`tests/test_scheduler.py`：
```python
from datetime import datetime


def test_trading_hours_gate():
    from server.refresh.scheduler import is_trading_hours
    assert is_trading_hours(datetime(2026, 6, 23, 10, 0)) is True   # 周二上午
    assert is_trading_hours(datetime(2026, 6, 23, 14, 0)) is True   # 周二下午
    assert is_trading_hours(datetime(2026, 6, 23, 12, 0)) is False  # 午休
    assert is_trading_hours(datetime(2026, 6, 23, 16, 0)) is False  # 盘后
    assert is_trading_hours(datetime(2026, 6, 27, 10, 0)) is False  # 周六


def test_build_scheduler_registers_jobs():
    from server.refresh.scheduler import build_scheduler
    sched = build_scheduler()
    job_ids = {j.id for j in sched.get_jobs()}
    assert {"intraday_snapshots", "eod_materialize"}.issubset(job_ids)
    assert not sched.running  # 仅构建不启动
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_scheduler.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server.refresh.scheduler'`）

- [ ] **Step 3: 实现 `scheduler.py`**

`server/refresh/scheduler.py`：
```python
"""后台刷新调度：盘中每 2min 拉快照（交易时段门控），收盘后物化评分。"""
from __future__ import annotations

from datetime import datetime, time

from apscheduler.schedulers.background import BackgroundScheduler

from server.refresh import snapshots, scores

_AM = (time(9, 30), time(11, 30))
_PM = (time(13, 0), time(15, 0))


def is_trading_hours(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    t = now.time()
    return (_AM[0] <= t <= _AM[1]) or (_PM[0] <= t <= _PM[1])


def _intraday_job() -> None:
    if not is_trading_hours(datetime.now()):
        return
    for fn in (snapshots.refresh_quotes, snapshots.refresh_sectors):
        try:
            fn()
        except Exception:  # noqa: BLE001 后台任务失败不影响其他
            pass


def _eod_job() -> None:
    try:
        scores.materialize_scores()
    except Exception:  # noqa: BLE001
        pass


def build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="Asia/Shanghai")
    sched.add_job(_intraday_job, "interval", minutes=2, id="intraday_snapshots")
    sched.add_job(_eod_job, "cron", hour=15, minute=30, id="eod_materialize")
    return sched
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_scheduler.py -v`
Expected: PASS

- [ ] **Step 5: 接入 app lifespan**

修改 `server/app.py` 为：
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.routers import health


def create_app(start_scheduler: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        sched = None
        if start_scheduler:
            from server.refresh.scheduler import build_scheduler
            sched = build_scheduler()
            sched.start()
        try:
            yield
        finally:
            if sched is not None:
                sched.shutdown(wait=False)

    app = FastAPI(title="Aquant API", version="2.0", lifespan=lifespan)
    app.include_router(health.router)
    return app
```

- [ ] **Step 6: 回归测试（health 用例仍过，调度器关闭路径）**

Run: `python3 -m pytest tests/test_health.py tests/test_scheduler.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add server/refresh/scheduler.py server/app.py tests/test_scheduler.py
git commit -m "feat(refresh): APScheduler 交易时段门控 + lifespan 启停

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: 驾驶舱「大盘总览」端点

**Files:**
- Create: `server/schemas/__init__.py`, `server/schemas/cockpit.py`, `server/routers/cockpit.py`
- Modify: `server/app.py`（include cockpit router）
- Test: `tests/test_cockpit_api.py`

**Interfaces:**
- Consumes: `aquant.market.breadth() -> dict`、`aquant.market.regime() -> dict`、`aquant.market.index_trend(code="sh000300") -> dict`
- Produces: `GET /api/cockpit/overview` → `OverviewResp{breadth: dict, regime: dict, index: dict}`

- [ ] **Step 1: 写失败测试（mock 领域函数避免联网）**

`tests/test_cockpit_api.py`：
```python
def test_overview(client, monkeypatch):
    from aquant import market
    monkeypatch.setattr(market, "breadth", lambda: {"up": 2500, "down": 1800})
    monkeypatch.setattr(market, "regime", lambda: {"state": "均衡", "score": 0.5})
    monkeypatch.setattr(market, "index_trend", lambda code="sh000300": {"code": code, "close": 3900.0})
    r = client.get("/api/cockpit/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["breadth"]["up"] == 2500
    assert body["regime"]["state"] == "均衡"
    assert body["index"]["close"] == 3900.0
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_cockpit_api.py::test_overview -v`
Expected: FAIL（404 或 import error）

- [ ] **Step 3: 写 schema**

`server/schemas/cockpit.py`：
```python
from pydantic import BaseModel


class OverviewResp(BaseModel):
    breadth: dict
    regime: dict
    index: dict
```

`server/schemas/__init__.py`：空文件。

- [ ] **Step 4: 写 cockpit 路由**

`server/routers/cockpit.py`：
```python
from fastapi import APIRouter

from aquant import market
from server.schemas.cockpit import OverviewResp

router = APIRouter(prefix="/api/cockpit", tags=["cockpit"])


@router.get("/overview", response_model=OverviewResp)
def overview() -> OverviewResp:
    return OverviewResp(
        breadth=market.breadth(),
        regime=market.regime(),
        index=market.index_trend(),
    )
```

- [ ] **Step 5: 注册路由**

`server/app.py` 中 `from server.routers import health` 改为 `from server.routers import health, cockpit`，并在 `app.include_router(health.router)` 后加 `app.include_router(cockpit.router)`。

- [ ] **Step 6: 运行确认通过**

Run: `python3 -m pytest tests/test_cockpit_api.py::test_overview -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add server/schemas server/routers/cockpit.py server/app.py tests/test_cockpit_api.py
git commit -m "feat(cockpit): 大盘总览端点 /api/cockpit/overview

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: 驾驶舱「板块 + 资金流」端点

**Files:**
- Modify: `server/schemas/cockpit.py`、`server/routers/cockpit.py`
- Test: `tests/test_cockpit_api.py`（追加）

**Interfaces:**
- Consumes: `aquant.sector.rotation(top=10) -> dict`；`server.refresh.snapshots` 写入的 `sector_snapshot`（读最新 ts）
- Produces: `GET /api/cockpit/sectors` → `SectorsResp{as_of: str | None, rows: list[dict], rotation: dict}`（`rows` = 最新 ts 的板块快照按 pct_chg 降序）

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_cockpit_api.py`：
```python
import pandas as pd


def test_sectors(client, seed_db, monkeypatch):
    from server.refresh import snapshots
    from aquant import sector
    snapshots.refresh_sectors(fetch=lambda: pd.DataFrame(
        {"sector": ["银行", "煤炭"], "pct_chg": [1.1, -0.3], "mkt_cap": [5e11, 2e11]}))
    monkeypatch.setattr(sector, "rotation", lambda top=10: {"leaders": ["银行"]})
    r = client.get("/api/cockpit/sectors")
    assert r.status_code == 200
    body = r.json()
    assert body["rows"][0]["sector"] == "银行"      # pct_chg 最高在前
    assert body["rotation"]["leaders"] == ["银行"]
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_cockpit_api.py::test_sectors -v`
Expected: FAIL（404）

- [ ] **Step 3: 加 schema**

`server/schemas/cockpit.py` 追加：
```python
class SectorsResp(BaseModel):
    as_of: str | None
    rows: list[dict]
    rotation: dict
```

- [ ] **Step 4: 加路由 + 读快照辅助**

`server/routers/cockpit.py` 顶部加 `from aquant import sector` 与 `from aquant.data import store`，并追加：
```python
from server.schemas.cockpit import SectorsResp


@router.get("/sectors", response_model=SectorsResp)
def sectors() -> SectorsResp:
    rows, as_of = [], None
    if store.has_table("sector_snapshot"):
        df = store.query(
            "SELECT * FROM sector_snapshot "
            "WHERE ts = (SELECT max(ts) FROM sector_snapshot) "
            "ORDER BY pct_chg DESC")
        if not df.empty:
            as_of = str(df["ts"].iloc[0])
            rows = df.drop(columns=["ts"]).to_dict(orient="records")
    return SectorsResp(as_of=as_of, rows=rows, rotation=sector.rotation())
```

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_cockpit_api.py::test_sectors -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add server/schemas/cockpit.py server/routers/cockpit.py tests/test_cockpit_api.py
git commit -m "feat(cockpit): 板块快照+轮动端点 /api/cockpit/sectors

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: 驾驶舱「推荐一览 + 高分股」端点

**Files:**
- Modify: `server/schemas/cockpit.py`、`server/routers/cockpit.py`
- Test: `tests/test_cockpit_api.py`（追加）

**Interfaces:**
- Consumes: `server.refresh.scores.read_top_scores(top)`（Task 5）；`aquant.research.daily_picks(top=3) -> pd.DataFrame`
- Produces:
  - `GET /api/cockpit/top-scores?top=20` → `TopScoresResp{as_of: str | None, rows: list[dict]}`
  - `GET /api/cockpit/picks?top=3` → `PicksResp{rows: list[dict]}`

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_cockpit_api.py`：
```python
def test_top_scores(client, seed_db):
    from server.refresh import scores
    scores.materialize_scores()
    r = client.get("/api/cockpit/top-scores?top=1")
    assert r.status_code == 200
    body = r.json()
    assert len(body["rows"]) == 1
    assert "score" in body["rows"][0]


def test_picks(client, seed_db, monkeypatch):
    import pandas as pd
    from aquant import research
    monkeypatch.setattr(research, "daily_picks",
                        lambda **k: pd.DataFrame([{"code": "600000", "name": "浦发", "score": 1.2}]))
    r = client.get("/api/cockpit/picks?top=3")
    assert r.status_code == 200
    assert r.json()["rows"][0]["code"] == "600000"
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_cockpit_api.py::test_top_scores tests/test_cockpit_api.py::test_picks -v`
Expected: FAIL（404）

- [ ] **Step 3: 加 schema**

`server/schemas/cockpit.py` 追加：
```python
class TopScoresResp(BaseModel):
    as_of: str | None
    rows: list[dict]


class PicksResp(BaseModel):
    rows: list[dict]
```

- [ ] **Step 4: 加路由**

`server/routers/cockpit.py` 追加（顶部加 `from aquant import research`、`from server.refresh import scores`）：
```python
from server.schemas.cockpit import TopScoresResp, PicksResp


@router.get("/top-scores", response_model=TopScoresResp)
def top_scores(top: int = 20) -> TopScoresResp:
    df = scores.read_top_scores(top=top)
    as_of = str(df["as_of"].iloc[0]) if not df.empty else None
    rows = df.drop(columns=["as_of"]).to_dict(orient="records") if not df.empty else []
    return TopScoresResp(as_of=as_of, rows=rows)


@router.get("/picks", response_model=PicksResp)
def picks(top: int = 3) -> PicksResp:
    df = research.daily_picks(top=top)
    rows = df.to_dict(orient="records") if not df.empty else []
    return PicksResp(rows=rows)
```

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_cockpit_api.py -v`
Expected: PASS（全部 cockpit 用例）

- [ ] **Step 6: 提交**

```bash
git add server/schemas/cockpit.py server/routers/cockpit.py tests/test_cockpit_api.py
git commit -m "feat(cockpit): 推荐+高分股端点 top-scores/picks

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: 个股下钻端点（K线 + 研判报告）

**Files:**
- Create: `server/routers/stock.py`, `server/schemas/stock.py`
- Modify: `server/app.py`（include stock router）
- Test: `tests/test_stock_api.py`

**Interfaces:**
- Consumes: `aquant.data.store.load_daily(code) -> pd.DataFrame`；`aquant.research.decision(code) -> dict`
- Produces:
  - `GET /api/stock/{code}/kline?n=250` → `KlineResp{code: str, bars: list[dict]}`（`bars` 列 `[date,open,high,low,close,volume]`，取最近 n 根）
  - `GET /api/stock/{code}/report` → `ReportResp{code: str, decision: dict}`

- [ ] **Step 1: 写失败测试**

`tests/test_stock_api.py`：
```python
def test_kline(client, seed_db):
    r = client.get("/api/stock/600000/kline?n=10")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "600000"
    assert len(body["bars"]) == 10
    assert {"date", "open", "high", "low", "close", "volume"} <= set(body["bars"][0])


def test_report(client, seed_db, monkeypatch):
    from aquant import research
    monkeypatch.setattr(research, "decision", lambda code, rep=None: {"code": code, "signal": "持有/观望"})
    r = client.get("/api/stock/600000/report")
    assert r.status_code == 200
    assert r.json()["decision"]["signal"] == "持有/观望"
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_stock_api.py -v`
Expected: FAIL（404）

- [ ] **Step 3: 写 schema**

`server/schemas/stock.py`：
```python
from pydantic import BaseModel


class KlineResp(BaseModel):
    code: str
    bars: list[dict]


class ReportResp(BaseModel):
    code: str
    decision: dict
```

- [ ] **Step 4: 写 stock 路由**

`server/routers/stock.py`：
```python
from fastapi import APIRouter, HTTPException

from aquant import research
from aquant.data import store
from server.schemas.stock import KlineResp, ReportResp

router = APIRouter(prefix="/api/stock", tags=["stock"])

_BAR_COLS = ["date", "open", "high", "low", "close", "volume"]


@router.get("/{code}/kline", response_model=KlineResp)
def kline(code: str, n: int = 250) -> KlineResp:
    df = store.load_daily(code)
    if df.empty:
        raise HTTPException(status_code=404, detail="no data")
    bars = df[[c for c in _BAR_COLS if c in df.columns]].tail(n).to_dict(orient="records")
    return KlineResp(code=code, bars=bars)


@router.get("/{code}/report", response_model=ReportResp)
def report(code: str) -> ReportResp:
    d = research.decision(code)
    if not d:
        raise HTTPException(status_code=404, detail="no data")
    return ReportResp(code=code, decision=d)
```

- [ ] **Step 5: 注册路由**

`server/app.py` 的 import 改为 `from server.routers import health, cockpit, stock`，并加 `app.include_router(stock.router)`。

- [ ] **Step 6: 运行确认通过**

Run: `python3 -m pytest tests/test_stock_api.py -v`
Expected: PASS

- [ ] **Step 7: 全量回归 + 提交**

```bash
python3 -m pytest -v
git add server/routers/stock.py server/schemas/stock.py server/app.py tests/test_stock_api.py
git commit -m "feat(stock): 个股下钻端点 kline/report

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 11: 本地启动脚本 + 冒烟验证

**Files:**
- Create: `server/__main__.py`
- Modify: `README.md`（追加 v2 后端启动段）

**Interfaces:**
- Produces: `python3 -m server` 启动 uvicorn（默认 8000 端口，含调度器）

- [ ] **Step 1: 写启动入口**

`server/__main__.py`：
```python
import uvicorn

from server.app import create_app

if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
```

- [ ] **Step 2: 冒烟启动（后台）并验证健康检查**

```bash
cd /Volumes/demon/code/ml/study/stock
nohup python3 -m server > data_store/api.log 2>&1 &
sleep 5
curl -s http://127.0.0.1:8000/api/health
```
Expected: 返回 JSON，`"status":"ok"`，`latest_bar_date` 为真实库最新日（连真实 `market.duckdb`，因未设 `AQUANT_DATA_DIR`）。

- [ ] **Step 3: 验证驾驶舱端点不联网阻塞（应秒回，物化表存在时）**

```bash
python3 -c "from server.refresh import scores; print('materialized rows:', scores.materialize_scores())"
time curl -s "http://127.0.0.1:8000/api/cockpit/top-scores?top=10" | head -c 200
```
Expected: `materialize_scores` 打印行数；curl 在 1s 内返回前 10 高分股 JSON。

- [ ] **Step 4: 关停冒烟进程**

```bash
pkill -f "python3 -m server"
```

- [ ] **Step 5: README 追加启动说明 + 提交**

`README.md` 末尾追加：
```markdown
## v2 后端（FastAPI）

    python3 -m server          # 启动 API + 后台刷新调度（127.0.0.1:8000）
    curl localhost:8000/api/health

端点：/api/cockpit/overview · /sectors · /top-scores · /picks · /api/stock/{code}/kline · /report
```

```bash
git add server/__main__.py README.md
git commit -m "feat(server): 本地启动入口 + README v2 后端说明

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照设计文档第 1–4 节，阶段1 后端部分）：
- 铁律"API 不在请求内联网" → Task 7–10 端点只读库/调 mock 的领域函数；快照/物化由 Task 3–6 后台任务负责。✅
- 数据分层：盘中快照（quote/sector，Task 3/4）、批量物化评分（Task 5）、调度门控（Task 6）。✅
- 物化评分降 30–60s→ms → Task 5 + Task 11 Step 3 冒烟验证。✅
- 驾驶舱"总"层数据（大盘/板块/资金/推荐收益/高分） → Task 7–9。✅
- 驾驶舱"分"层下钻（个股K图/研判） → Task 10。✅
- 指数快照表 `index_snapshot`：阶段1 大盘用 `market.index_trend()`（基于 `index_daily`）即可满足，**盘中指数快照延后到前端 Plan 1B 或阶段2**，不在本计划范围（避免过度构建）。
- 市场情绪/北向、量化交易一览（因子IC状态）：设计列为驾驶舱内容，但依赖现成数据较少，**延后**到 1B 接线时按需补端点，本计划不强行造。

**占位符扫描**：无 TBD/TODO；每个代码步骤均含完整可运行代码。✅

**类型一致性**：`refresh_quotes`/`refresh_sectors`(返回 int)、`materialize_scores`(int)/`read_top_scores`(DataFrame)、`is_trading_hours`(bool)/`build_scheduler`(BackgroundScheduler)、各端点 `response_model` 与 schema 字段一致；`spot_snapshot` 列契约与 Task 3 消费一致。✅

**范围**：聚焦后端单一可测子系统（pytest 全绿 + 冒烟）。前端为独立 Plan 1B。✅
