# Phase 3A — 量化后端（异步回测 + 因子IC）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现量化闭环后端：异步任务运行器（提交/轮询，DuckDB 落状态）+ 向量化回测任务 + 因子 IC 任务 + 端点，全部只读库/无请求内联网/不阻塞请求。

**Architecture:** 领域逻辑放 `aquant/quant/jobs.py`：`quant_jobs` 表存任务状态/结果；`submit_job` 写 pending 并按同步标志（测试）或线程池（生产）派发 `run_job`；`run_job` 按 kind 分派到 `_run_backtest`/`_run_factor_ic`（复用 `scorer.score_panel`+`backtest_topn`+`perf_metrics`、`factor_eval.evaluate`）。FastAPI 路由薄封装提交/轮询。

**Tech Stack:** Python 3.11 · FastAPI · DuckDB（`aquant.data.store`）· concurrent.futures 线程池 · pytest + httpx TestClient。

## Global Constraints

- Python 3.11；复用现有 `aquant/backtest`、`aquant/select/scorer`，不重写算法；量化任务逻辑放 `aquant/quant/`。
- DB 路径由 `AQUANT_DATA_DIR` 驱动；测试在 import 任何 `aquant` 前设置（沿用 `tests/conftest.py`）。
- 任务确定性测试：jobs 模块读环境变量 `AQUANT_JOBS_SYNC`——为 `"1"` 时 `submit_job` 内**同步**执行 `run_job`（不起线程），否则提交到线程池。`tests/conftest.py` 在模块顶部设 `os.environ["AQUANT_JOBS_SYNC"] = "1"`（须在 import aquant 前）。
- 新表在 `store.TABLE_KEYS` 注册主键。
- API 请求处理与任务线程内**禁止**第三方网络调用；只读写本地库 + 复用领域函数。
- 端点路径以 `/api/quant` 前缀；JSON 响应用 pydantic 模型。
- 结果中的 DataFrame/Series 一律转 JSON 友好结构（records / list）后存 `result_json`（字符串）。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `phase3a-backend` 上开发；每个 Task 末尾提交。
- 复用契约（现有代码，已核对）：
  - `aquant.select.scorer.score_panel(codes, weights=None, min_history=250) -> (price, total)`：两个 index=date、columns=code 宽表。
  - `aquant.select.scorer.IC_WEIGHTS`、`MOMENTUM_WEIGHTS`（dict[str,float]）。
  - `aquant.backtest.engine.backtest_topn(price_panel, score_panel, top=5, rebalance=5, fee=0.0013, ...) -> {"metrics":dict, "equity":pd.Series, "weights":pd.DataFrame}`；`equity` index=date。`metrics` 含 total_return/annual_return/annual_vol/sharpe/max_drawdown/calmar/win_rate/days/benchmark_return。
  - `aquant.backtest.factor_eval.evaluate(codes, factors=None, fwd=5) -> pd.DataFrame`（列：factor/ic_mean/ic_std/ir/ic_win/n；按 |ir| 排序）。
  - `aquant.research.universe(drop_boards=None) -> list[str]`；`aquant.data.store.save/query/has_table`。

---

### Task 1: quant_jobs 表 + 任务运行器内核

**Files:**
- Create: `aquant/quant/__init__.py`, `aquant/quant/jobs.py`, `tests/test_quant_jobs.py`
- Modify: `aquant/data/store.py`（`TABLE_KEYS` 加 `quant_jobs`）, `tests/conftest.py`（设 `AQUANT_JOBS_SYNC=1`）

**Interfaces:**
- Produces：
  - `aquant.quant.jobs.register(kind: str, fn)`（注册 kind→runner(params)->dict）
  - `submit_job(kind: str, params: dict) -> str`（写 pending 行；按 `AQUANT_JOBS_SYNC` 同步或线程派发 `run_job`；返回 job_id=uuid4 hex）
  - `run_job(job_id: str) -> None`（置 running→调对应 runner→写 result_json+status=done；异常写 error+status=error）
  - `get_job(job_id: str) -> dict | None`（读一行，`result` 解析回 dict/None）

- [ ] **Step 1: 注册表主键 + conftest 同步标志**

`aquant/data/store.py` 的 `TABLE_KEYS` 内新增：
```python
    "quant_jobs": ["job_id"],
```
`tests/conftest.py` 顶部（在 `os.environ["AQUANT_DATA_DIR"] = _TMP` 之后、import aquant 之前）新增：
```python
os.environ["AQUANT_JOBS_SYNC"] = "1"
```

- [ ] **Step 2: 写失败测试（用 dummy runner 隔离内核）**

`tests/test_quant_jobs.py`：
```python
def test_submit_run_get_lifecycle(seed_db):
    from aquant.quant import jobs
    jobs.register("echo", lambda params: {"echoed": params["x"] * 2})
    jid = jobs.submit_job("echo", {"x": 21})
    # AQUANT_JOBS_SYNC=1 → submit 内已同步跑完
    job = jobs.get_job(jid)
    assert job["status"] == "done"
    assert job["kind"] == "echo"
    assert job["result"] == {"echoed": 42}


def test_job_error_captured(seed_db):
    from aquant.quant import jobs
    def boom(params):
        raise ValueError("nope")
    jobs.register("boom", boom)
    jid = jobs.submit_job("boom", {})
    job = jobs.get_job(jid)
    assert job["status"] == "error"
    assert "nope" in job["error"]


def test_get_missing_job(seed_db):
    from aquant.quant import jobs
    assert jobs.get_job("nosuch") is None
```

- [ ] **Step 3: 运行确认失败**

Run: `python3 -m pytest tests/test_quant_jobs.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'aquant.quant'`）

- [ ] **Step 4: 实现 `jobs.py`**

`aquant/quant/jobs.py`：
```python
"""量化异步任务运行器：DuckDB 落状态，线程池执行（测试可同步）。"""
from __future__ import annotations

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable

import pandas as pd

from ..data import store

_SYNC = os.getenv("AQUANT_JOBS_SYNC") == "1"
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="quantjob")
_RUNNERS: dict[str, Callable[[dict], dict]] = {}


def register(kind: str, fn: Callable[[dict], dict]) -> None:
    _RUNNERS[kind] = fn


def _write(row: dict) -> None:
    store.save("quant_jobs", pd.DataFrame([row]))


def submit_job(kind: str, params: dict) -> str:
    job_id = uuid.uuid4().hex
    _write({"job_id": job_id, "kind": kind, "params_json": json.dumps(params),
            "status": "pending", "result_json": None, "error": None,
            "created_ts": datetime.now().isoformat(timespec="seconds")})
    if _SYNC:
        run_job(job_id)
    else:
        _EXECUTOR.submit(run_job, job_id)
    return job_id


def _row(job_id: str) -> dict | None:
    df = store.query("SELECT * FROM quant_jobs WHERE job_id = ?", [job_id])
    return df.iloc[0].to_dict() if not df.empty else None


def run_job(job_id: str) -> None:
    row = _row(job_id)
    if row is None:
        return
    kind, params = row["kind"], json.loads(row["params_json"])
    base = {"job_id": job_id, "kind": kind, "params_json": row["params_json"],
            "created_ts": row["created_ts"]}
    try:
        fn = _RUNNERS[kind]
        result = fn(params)
        _write({**base, "status": "done", "result_json": json.dumps(result), "error": None})
    except Exception as e:  # noqa: BLE001 任务失败要落库，不可吞
        _write({**base, "status": "error", "result_json": None, "error": str(e)[:500]})


def get_job(job_id: str) -> dict | None:
    row = _row(job_id)
    if row is None:
        return None
    result = json.loads(row["result_json"]) if row.get("result_json") else None
    return {"job_id": job_id, "kind": row["kind"], "status": row["status"],
            "result": result, "error": row.get("error"), "created_ts": row["created_ts"]}
```
`aquant/quant/__init__.py`：空文件。

- [ ] **Step 5: 运行确认通过**

Run: `python3 -m pytest tests/test_quant_jobs.py -v`
Expected: PASS（3 tests）

- [ ] **Step 6: 提交**

```bash
git add aquant/quant aquant/data/store.py tests/test_quant_jobs.py tests/conftest.py
git commit -m "feat(quant): quant_jobs 表 + 异步任务运行器内核

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 回测任务 `_run_backtest`

**Files:**
- Create: `aquant/quant/backtest_job.py`
- Modify: `aquant/quant/__init__.py`（import 触发注册）
- Test: `tests/test_backtest_job.py`

**Interfaces:**
- Consumes: `scorer.score_panel`、`scorer.IC_WEIGHTS`/`MOMENTUM_WEIGHTS`、`backtest_topn`、`research.universe`、`store`
- Produces：
  - `aquant.quant.backtest_job.resolve_weights(weights) -> dict[str,float]`（`"ic"`→IC_WEIGHTS，`"momentum"`→MOMENTUM_WEIGHTS，dict→原样）
  - `run_backtest(params: dict) -> dict`（注册为 kind `"backtest"`），结果：
    `{"nav":[{"date","equity","benchmark"}], "metrics":dict, "top_n":int, "rebalance_every":int}`
  - import `aquant.quant.backtest_job` 时调用 `jobs.register("backtest", run_backtest)`

- [ ] **Step 1: 写失败测试（小样本 fixture，min_history 低）**

`tests/test_backtest_job.py`：
```python
def test_resolve_weights():
    from aquant.quant import backtest_job
    from aquant.select import scorer
    assert backtest_job.resolve_weights("ic") == scorer.IC_WEIGHTS
    assert backtest_job.resolve_weights("momentum") == scorer.MOMENTUM_WEIGHTS
    assert backtest_job.resolve_weights({"mom_20": 1.0}) == {"mom_20": 1.0}


def test_run_backtest_smoke(seed_db):
    from aquant.quant import backtest_job
    out = backtest_job.run_backtest({"weights": "ic", "top_n": 2, "rebalance_every": 5, "min_history": 60})
    assert "metrics" in out and "nav" in out
    assert out["top_n"] == 2
    assert isinstance(out["nav"], list)
    if out["nav"]:
        assert set(out["nav"][0]) >= {"date", "equity"}


def test_backtest_registered():
    import aquant.quant.backtest_job  # noqa: F401 触发注册
    from aquant.quant import jobs
    assert "backtest" in jobs._RUNNERS
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_backtest_job.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 `backtest_job.py`**

`aquant/quant/backtest_job.py`：
```python
"""回测任务：解析权重 → score_panel → backtest_topn → 净值+绩效（含基准曲线）。"""
from __future__ import annotations

import pandas as pd

from ..backtest.engine import backtest_topn
from ..data import store
from ..select import scorer
from .. import research
from . import jobs


def resolve_weights(weights) -> dict:
    if weights == "ic":
        return scorer.IC_WEIGHTS
    if weights == "momentum":
        return scorer.MOMENTUM_WEIGHTS
    if isinstance(weights, dict) and weights:
        return weights
    return scorer.IC_WEIGHTS


def _benchmark_series(dates: pd.Index) -> dict[str, float]:
    """沪深300 归一化到 1.0 的基准曲线（对齐回测日期）；无数据返回空。"""
    if not store.has_table("index_daily"):
        return {}
    idx = store.query("SELECT date, close FROM index_daily WHERE code = 'sh000300' ORDER BY date")
    if idx.empty:
        return {}
    s = idx.set_index("date")["close"].reindex([str(d) for d in dates]).ffill()
    base = s.dropna()
    if base.empty:
        return {}
    return (s / base.iloc[0]).to_dict()


def run_backtest(params: dict) -> dict:
    weights = resolve_weights(params.get("weights", "ic"))
    top_n = int(params.get("top_n", 5))
    rebalance = int(params.get("rebalance_every", 5))
    min_history = int(params.get("min_history", 250))
    codes = research.universe(drop_boards=set(params["drop_boards"]) if params.get("drop_boards") else None)
    price, score = scorer.score_panel(codes, weights, min_history=min_history)
    if price.empty or score.empty:
        return {"nav": [], "metrics": {}, "top_n": top_n, "rebalance_every": rebalance}
    res = backtest_topn(price, score, top=top_n, rebalance=rebalance)
    equity = res["equity"].dropna()
    bench = _benchmark_series(equity.index)
    nav = [{"date": str(d), "equity": round(float(v), 4),
            "benchmark": round(float(bench[str(d)]), 4) if str(d) in bench else None}
           for d, v in equity.items()]
    return {"nav": nav, "metrics": res["metrics"], "top_n": top_n, "rebalance_every": rebalance}


jobs.register("backtest", run_backtest)
```
`aquant/quant/__init__.py` 追加（确保导入即注册）：
```python
from . import backtest_job  # noqa: F401
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_backtest_job.py -v`
Expected: PASS（3 tests）

- [ ] **Step 5: 提交**

```bash
git add aquant/quant/backtest_job.py aquant/quant/__init__.py tests/test_backtest_job.py
git commit -m "feat(quant): 回测任务 run_backtest（score_panel+topn+基准）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 因子 IC 任务 `_run_factor_ic`

**Files:**
- Create: `aquant/quant/factor_job.py`
- Modify: `aquant/quant/__init__.py`（import 触发注册）
- Test: `tests/test_factor_job.py`

**Interfaces:**
- Consumes: `factor_eval.evaluate`、`research.universe`
- Produces：
  - `aquant.quant.factor_job.run_factor_ic(params: dict) -> dict`（注册为 `"factor_ic"`），结果 `{"rows":[{factor,ic_mean,ic_std,ir,ic_win,n}], "fwd":int}`
  - import 时 `jobs.register("factor_ic", run_factor_ic)`

- [ ] **Step 1: 写失败测试**

`tests/test_factor_job.py`：
```python
def test_run_factor_ic_smoke(seed_db):
    from aquant.quant import factor_job
    out = factor_job.run_factor_ic({"factors": ["mom_20", "volatility_20"], "fwd": 5})
    assert "rows" in out and out["fwd"] == 5
    assert isinstance(out["rows"], list)


def test_factor_ic_registered():
    import aquant.quant.factor_job  # noqa: F401
    from aquant.quant import jobs
    assert "factor_ic" in jobs._RUNNERS
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_factor_job.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `factor_job.py`**

`aquant/quant/factor_job.py`：
```python
"""因子 IC 任务：对 universe 跑各因子 IC/IR 排名。"""
from __future__ import annotations

from ..backtest import factor_eval
from .. import research
from . import jobs


def run_factor_ic(params: dict) -> dict:
    fwd = int(params.get("fwd", 5))
    factors = params.get("factors")  # None → 全因子
    codes = research.universe()
    df = factor_eval.evaluate(codes, factors=factors, fwd=fwd)
    rows = df.to_dict(orient="records") if not df.empty else []
    return {"rows": rows, "fwd": fwd}


jobs.register("factor_ic", run_factor_ic)
```
`aquant/quant/__init__.py` 追加：
```python
from . import factor_job  # noqa: F401
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `python3 -m pytest tests/test_factor_job.py -v`
Expected: PASS

```bash
git add aquant/quant/factor_job.py aquant/quant/__init__.py tests/test_factor_job.py
git commit -m "feat(quant): 因子 IC 任务 run_factor_ic

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 量化 API 端点

**Files:**
- Create: `server/schemas/quant.py`, `server/routers/quant.py`, `tests/test_quant_api.py`
- Modify: `server/app.py`（include quant router）

**Interfaces:**
- Consumes: `aquant.quant.jobs`（submit_job/get_job）；`aquant.quant`（导入触发任务注册）；`scorer.IC_WEIGHTS`/`MOMENTUM_WEIGHTS`
- Produces：
  - `POST /api/quant/backtest` body `BacktestIn{capital?,weights?,top_n?,rebalance_every?,start?,end?,min_history?}` → `{job_id}`
  - `GET /api/quant/backtest/{job_id}` → `JobResp{job_id,kind,status,result,error}`
  - `POST /api/quant/factor-ic` body `FactorIcIn{factors?,fwd?}` → `{job_id}`
  - `GET /api/quant/factor-ic/{job_id}` → `JobResp`
  - `GET /api/quant/weights` → `WeightsResp{ic:dict, momentum:dict}`

- [ ] **Step 1: 写失败测试（AQUANT_JOBS_SYNC=1 → 提交即完成）**

`tests/test_quant_api.py`：
```python
def test_weights_presets(client):
    r = client.get("/api/quant/weights")
    assert r.status_code == 200
    body = r.json()
    assert "ic" in body and "momentum" in body and isinstance(body["ic"], dict)


def test_backtest_submit_then_poll(client, seed_db):
    r = client.post("/api/quant/backtest", json={"weights": "ic", "top_n": 2, "rebalance_every": 5, "min_history": 60})
    assert r.status_code == 200
    jid = r.json()["job_id"]
    g = client.get(f"/api/quant/backtest/{jid}")
    assert g.status_code == 200
    body = g.json()
    assert body["status"] == "done"          # 同步模式提交即完成
    assert "metrics" in body["result"] and "nav" in body["result"]


def test_factor_ic_submit_then_poll(client, seed_db):
    r = client.post("/api/quant/factor-ic", json={"factors": ["mom_20", "volatility_20"], "fwd": 5})
    jid = r.json()["job_id"]
    body = client.get(f"/api/quant/factor-ic/{jid}").json()
    assert body["status"] == "done"
    assert "rows" in body["result"]


def test_unknown_job_404(client):
    assert client.get("/api/quant/backtest/nosuch").status_code == 404
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_quant_api.py -v`
Expected: FAIL（404 / import error）

- [ ] **Step 3: 写 schema**

`server/schemas/quant.py`：
```python
from pydantic import BaseModel


class BacktestIn(BaseModel):
    capital: float = 1_000_000
    weights: object = "ic"          # "ic"/"momentum" 或 {factor: weight}
    top_n: int = 5
    rebalance_every: int = 5
    start: str | None = None
    end: str | None = None
    min_history: int = 250


class FactorIcIn(BaseModel):
    factors: list[str] | None = None
    fwd: int = 5


class JobCreated(BaseModel):
    job_id: str


class JobResp(BaseModel):
    job_id: str
    kind: str
    status: str
    result: dict | None = None
    error: str | None = None


class WeightsResp(BaseModel):
    ic: dict
    momentum: dict
```

- [ ] **Step 4: 写路由**

`server/routers/quant.py`：
```python
from fastapi import APIRouter, HTTPException

import aquant.quant  # noqa: F401 触发 backtest/factor_ic 任务注册
from aquant.quant import jobs
from aquant.select import scorer
from server.schemas.quant import BacktestIn, FactorIcIn, JobCreated, JobResp, WeightsResp

router = APIRouter(prefix="/api/quant", tags=["quant"])


@router.get("/weights", response_model=WeightsResp)
def weights() -> WeightsResp:
    return WeightsResp(ic=dict(scorer.IC_WEIGHTS), momentum=dict(scorer.MOMENTUM_WEIGHTS))


@router.post("/backtest", response_model=JobCreated)
def submit_backtest(body: BacktestIn) -> JobCreated:
    return JobCreated(job_id=jobs.submit_job("backtest", body.model_dump()))


@router.post("/factor-ic", response_model=JobCreated)
def submit_factor_ic(body: FactorIcIn) -> JobCreated:
    return JobCreated(job_id=jobs.submit_job("factor_ic", body.model_dump()))


def _job_or_404(job_id: str, kind: str) -> JobResp:
    job = jobs.get_job(job_id)
    if job is None or job["kind"] != kind:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResp(**job)


@router.get("/backtest/{job_id}", response_model=JobResp)
def backtest_status(job_id: str) -> JobResp:
    return _job_or_404(job_id, "backtest")


@router.get("/factor-ic/{job_id}", response_model=JobResp)
def factor_ic_status(job_id: str) -> JobResp:
    return _job_or_404(job_id, "factor_ic")
```

- [ ] **Step 5: 注册路由**

`server/app.py` 的 routers import 行加入 `quant`，并加 `app.include_router(quant.router)`。

- [ ] **Step 6: 运行确认通过 + 全量回归**

Run: `python3 -m pytest tests/test_quant_api.py -v && python3 -m pytest -q`
Expected: quant 4 用例 PASS；全套（前序 26 + 新增量化）全绿。

- [ ] **Step 7: 提交**

```bash
git add server/schemas/quant.py server/routers/quant.py server/app.py tests/test_quant_api.py
git commit -m "feat(quant): 量化 API 端点（回测/因子IC 提交+轮询/权重预设）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照 Phase 3 设计第 1 节后端）：
- 异步任务运行器（quant_jobs 表 + submit/run/get + 同步标志测试）→ Task 1。✅
- 回测任务（权重解析 + score_panel + backtest_topn + 基准曲线 + perf_metrics）→ Task 2。✅
- 因子 IC 任务（factor_eval.evaluate）→ Task 3。✅
- 5 端点（backtest/factor-ic 提交+轮询、weights 预设）→ Task 4。✅
- 铁律：任务线程内只读库 + 复用领域函数，无联网；结果序列化存库。✅

**占位符扫描**：无 TBD/TODO；每步含完整可运行代码。✅

**类型一致性**：`register/submit_job/run_job/get_job` 在内核与任务模块、路由间一致；`run_backtest`/`run_factor_ic` 返回结构与端点 `JobResp.result`(dict) 一致；`resolve_weights` 入参（str/dict）与 `BacktestIn.weights`(object) 一致；端点 `response_model` 与 schema 字段一致。✅

**范围**：单一可测后端子系统（pytest 全绿）。前端为独立 Plan 3B。✅

**已知风险/前提**：
- `score_panel` 默认 `min_history=250`，小样本 fixture（80 日）会被过滤为空 → 回测测试显式传 `min_history=60`，且 `run_backtest` 对空面板返回空结果（不报错）。真实使用走默认 250。
- `AQUANT_JOBS_SYNC=1` 仅测试环境设置；生产经线程池异步，前端轮询。
- 线程池 `submit(run_job)` 的 orphan 线程在重计算时长期占用——单用户可接受；`max_workers=2` 限并发。
