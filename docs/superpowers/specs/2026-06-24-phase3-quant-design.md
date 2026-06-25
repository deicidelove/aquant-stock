# Phase 3 量化闭环 · 设计文档

- 日期：2026-06-24
- 状态：已确认（待写实现计划）
- 范围：v2 重构总纲的「板块③ 量化」。一个子系统，分后端/前端两期实现。
- 上游：[v2 重构总纲](2026-06-23-stock-system-v2-redesign.md)；Phase 1（驾驶舱）、Phase 2（辅助股民）已合并。

## 目标

把因子研究 / 回测 / 模拟串成量化闭环：

```
初始金额 → 选因子/权重 → 回测(模拟实战) → 收益分析 → 优化因子 → 再回测 …
   │           │              │              │           │
 capital   IC/动量/自定义   backtest_topn   净值+绩效    因子IC排名
                          (异步任务)        +基准对比    (factor_eval)
```

核心引擎 = `backtest_topn`（向量化 Top-N 组合回测），几乎全是复用现有量化模块，不造新算法。

## 关键决策（已与用户确认）

| 维度 | 决策 |
|---|---|
| 模拟引擎 | 向量化回测为主（`backtest_topn`）；持久模拟盘 paper 留作后续 |
| 回测计算 | 异步任务（提交→轮询），不阻塞请求 |
| 复用 | `aquant/backtest/engine.py`(`backtest_topn`/`perf_metrics`)、`backtest/factor_eval.py`(`evaluate`/`composite_score_panel`)、`scorer`(IC_WEIGHTS/MOMENTUM_WEIGHTS) |

## 架构铁律（沿用 v2 总纲）

任务线程内只读 DuckDB 与复用领域函数，无第三方联网；API 提交/轮询端点只读写本地库。

## 第 1 节 · 后端（Plan 3A）

### 异步任务运行器

单用户本地：后台线程执行 + DuckDB 落状态（重启可见、符合"库为真相源"）。

- 新表 `quant_jobs`，`TABLE_KEYS=["job_id"]`：`job_id`(uuid 字符串)、`kind`(backtest|factor_ic)、`params_json`、`status`(pending/running/done/error)、`result_json`、`error`、`created_ts`。
- 提交：写一行 status=pending → 提交到 `ThreadPoolExecutor` 跑 → 运行中置 running → 完成写 result_json/status=done（异常写 error/status=error）。
- 轮询：按 job_id 读状态与结果。
- 领域逻辑放 `aquant/quant/jobs.py`（`submit_job(kind, params) -> job_id`、`run_job(job_id)`、`get_job(job_id) -> dict`、`_run_backtest(params)`、`_run_factor_ic(params)`），可单测（同步调用 run_job 后读结果，不依赖线程时序）。

### 任务类型

- **backtest** 入参 `{capital, weights, top_n, rebalance_every, start, end, drop_boards?}`：
  - `weights`：预设名（`"ic"`/`"momentum"`）或自定义 `{factor: weight}`；解析为权重 dict。
  - 流程：`universe(drop_boards)` → `composite_score_panel(codes, weights)` 得 score 面板 + 价格面板 → `backtest_topn(price, score, top_n, rebalance_every, capital, start, end)` → `perf_metrics`。
  - 结果 `{nav:[{date,equity,benchmark}], metrics:{annual,sharpe,max_drawdown,win_rate,...}, top_n, rebalance_every}`。
- **factor_ic** 入参 `{factors?, fwd}`：`factor_eval.evaluate(universe(), factors, fwd)` → 各因子 IC 均值/IR 排名 → 结果 `{rows:[{factor, ic_mean, ir, ...}]}`。

### 端点

| 方法 路径 | 作用 |
|---|---|
| `POST /api/quant/backtest` | 提交回测任务 → `{job_id}` |
| `GET /api/quant/backtest/{job_id}` | 回测任务状态+结果 |
| `POST /api/quant/factor-ic` | 提交因子 IC 任务 → `{job_id}` |
| `GET /api/quant/factor-ic/{job_id}` | 因子 IC 任务状态+结果 |
| `GET /api/quant/weights` | 预设权重（IC_WEIGHTS / MOMENTUM_WEIGHTS）供前端编辑起点 |

## 第 2 节 · 前端（Plan 3B）

新增"量化"板块（顶部导航入口 + `/quant` 路由），2 个页面：

- **回测** `/quant/backtest`：配置表单（初始金额 / 权重：预设下拉 + 可调各因子权重 / Top-N / 调仓周期 / 起止区间）→ 提交（POST）得 job_id → 轮询（TanStack `refetchInterval` 直到 status=done）显示 loading → 完成后渲染净值曲线（ECharts 折线：策略 vs 沪深300）+ 绩效卡（年化 / 夏普 / 最大回撤 / 胜率）。
- **因子** `/quant/factors`：提交因子 IC 任务 → 轮询 → IC/IR 排名（条形图 + 表）。点某因子可把其回填进回测页的权重起点（闭环到"调权重"）。

沿用 1B/2B 架构：纯展示组件 + TanStack Query（提交用 mutation，轮询用带 `refetchInterval` 的 query，job done 后停轮询）+ client 扩展。

## 第 3 节 · 分期

- **Plan 3A 后端**：`quant_jobs` 表 + 任务运行器（submit/run/get）+ backtest/factor_ic 两类任务 + 5 个端点；pytest（注入小样本，同步 `run_job` 后验证 result；端点 submit→done 流程）。
- **Plan 3B 前端**：量化板块 2 页面 + 提交/轮询；Vitest。

## 非目标（YAGNI）

- 不做多方案并排对比（跑两次即可）、不做参数自动寻优/网格搜索。
- 不接实盘、不做分布式/任务队列中间件（线程级足够单用户）。
- 持久模拟盘（paper account 前向跟踪）留作后续，本期以向量化回测为主。
- 回测单配置提交；不做批量扫描。

## 未决 / 计划阶段再定

- 回测默认区间与默认 universe 范围（控制单次任务耗时；必要时限定采样或近 N 年）。
- `quant_jobs` 旧任务清理策略（是否保留全部历史）。
- 线程执行器并发度（默认 1–2，避免重计算挤占）。
- factor_eval.evaluate / backtest_topn 的精确签名与返回列，计划阶段核对后写入。
