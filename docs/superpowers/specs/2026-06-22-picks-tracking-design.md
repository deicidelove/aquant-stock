# 每日推荐跟踪台账（picks tracking）设计

> 状态：已确认设计，待 spec 复核 → 实现计划
> 日期：2026-06-22

## 背景与问题

`run_daily` 每天调 `research.daily_picks` 生成推荐清单，但只落地为 `reports/decision_YYYY-MM-DD.md`（markdown 文件），**没有结构化留痕**。事后无法批量统计"过去推荐的票后来涨没涨"，导致：

- 推荐算法（scorer 的 IC 综合分）**只有回测 IC，没有实盘/样本外 live IC** 对照。
- 无法回答"算法到底准不准"，更谈不上持续学习优化。

现有 `paper` 模块跟踪的是**单一季度低波组合的净值**（仓位 + 现金约束），不是横截面"推荐信号有效性"评估，二者不可混用。

本设计搭**地基**：把每日推荐结构化落库，事后算前向收益，产出可与回测对照的 live Rank-IC 记分卡。不含自动调参 / ML（那是地基之上的后续工作）。

## 范围

**做**：推荐快照落库、历史回放冷启动、前向收益与记分卡评估、接入 run_daily、CLI、markdown 记分卡。

**不做**（YAGNI）：自动反馈调参、ML 模型训练、物化前向收益列、改动 scorer 选股逻辑。

## 架构决策

### 决策 1：轻量台账 + 评估时实时计算（不物化前向收益）

`picks_log` 只存推荐快照；前向收益不入库，评估时用 `entry_close` join `daily_bar` 现算。

理由：前向收益是 `(entry_close, 后续行情)` 的纯函数。物化会引入有状态的"每日结算"任务、窗口未到期的 NULL 回填、重算不一致风险。为省毫秒级计算引入状态不值（参见 README 研究发现"别为听起来高级的优化买单"）。单向写入、幂等。

**否决的替代**：
- 物化收益列 + 每日 settle 任务 —— 多一个有状态定时任务，易不一致。
- 复用 paper 账户灌 paper_trade —— paper 是单组合 + 现金约束，会把仓位配置和信号质量搅在一起；本需求要的是横截面信号有效性，与仓位无关。

### 决策 2：历史回放按周频（每 5 个交易日）

`reconstruct` 像 `paper.seed` 一样用历史数据回放近 1–2 年的当日推荐入库，但按**每 5 个交易日**取一个快照，而非每日。

理由：季度策略下日频快照高度重叠、样本自相关，污染 IC 统计；周频与季度持有口径不冲突，且立刻能产出几百条样本、上线当天即有 live IC，无需等月。

### 决策 3：核心指标 = Live Rank-IC + Top 分桶超额

记分卡头部指标：score 与前向收益的截面 Spearman 相关（Rank-IC），按 T+5/T+20/T+60 三档，逐快照日计算后取均值与 IR。直接与 README 回测 IC（IR）形成对照。

## 组件设计

### 数据层：新表 `picks_log`

| 列 | 类型 | 含义 |
|---|---|---|
| as_of | DATE | 推荐日（交易日） |
| code | TEXT | 标的代码 |
| name | TEXT | 标的名称 |
| rank | INT | 当日排名 |
| score | DOUBLE | IC 综合分 |
| action | TEXT | 动作（持有/空仓等） |
| signal | TEXT | 择时信号名 |
| entry_close | DOUBLE | 推荐日收盘价（前向收益基准） |

主键 `(as_of, code)`，经 `store.TABLE_KEYS` 注册后用 `store.save` upsert（与 paper 表同模式）。

### 模块 `aquant/track/`（与 paper 平级）

职责单一、互不耦合：log 只管"记录推荐了什么"，evaluate 无状态、仅对台账 + 行情做只读计算。

**`track/log.py`**
- `snapshot(as_of: str | None = None) -> int`
  - 调 `research.daily_picks` 取当日推荐，组装快照行写 `picks_log`，返回写入行数。
  - `entry_close` 取自当日 `daily_bar`。`as_of` 缺省=库内最新交易日。
- `reconstruct(start: str, every: int = 5, top: int = 30) -> dict`
  - 从 `start` 起按 `every` 个交易日为步长，复算当日 IC 综合分排名（复用 scorer 的截面 z-score 逻辑，参考 `paper.simulate._bulk_panels`），批量写 `picks_log`。
  - 返回 `{start, end, snapshots, rows}`。

**`track/evaluate.py`**（无状态，纯读）
- `forward_returns(horizons=(5, 20, 60)) -> pd.DataFrame`
  - 台账 join `daily_bar`：对每条推荐，找 `as_of` 后第 h 个交易日收盘价，算前向收益 `fwd_h = close_{t+h}/entry_close - 1`。
  - 减 `index_daily`（sh000300）同期收益得**超额** `exc_h`。
  - 窗口未到期 → 该档为 NaN，标 `pending`。
  - 停牌/退市 → 用最后可得价，置 flag。
- `scorecard() -> str`（markdown）
  - **Top-N 平均超额（外部有效性头号指标）**：所记录 Top-N 推荐相对沪深300 的平均前向超额 + 胜率（正超额占比），三档分列。这是"推荐到底赚不赚"的直接答案。
  - **Live Rank-IC（池内排序质量）**：逐 `as_of` 截面算 score 与 fwd_h 的 Spearman，跨日均值 + IR，三档分列，与 README 回测 IC 对照。
    - 注意：台账只存 Top-N，故 Rank-IC / 池内分桶价差只衡量**已推荐集合内部**的排序好坏，解释力有限（非全市场多空）；外部有效性以 Top-N 平均超额为准。
  - **覆盖与诚实标注**：样本数、日期范围、各档 pending 条数。

### 接入与输出

- `pipeline.run_daily` 末尾追加 `track.snapshot(day)`（用 `_safe` 包裹，失败不中断主流程），此后每日自动留痕。
- CLI（`aquant/cli.py`）新增：
  - `track-backfill [--start YYYYMMDD] [--every 5] [--top 30]` → `track.log.reconstruct`
  - `track-eval` → 打印并保存记分卡到 `reports/track_scorecard.md`
- 记分卡输出 `reports/track_scorecard.md`。

## 错误处理与边界

- **窗口未到期**：前向收益 NaN，计入 pending，不参与该档统计（避免幸存偏差污染均值）。
- **停牌/退市**：用最后可得收盘价，行打 flag；幸存者偏差延续 README 既定态度——标注而非假装解决。
- **数据不足**：`daily_bar` / `index_daily` 缺失时评估优雅降级（对应列留空 + 提示），不抛断。
- **selection universe**：回放与实时均复用 `research.universe()`，沿用 ST/次新/低流动性过滤口径，保证回测/实盘可比。

## 测试策略

- `track.log.snapshot`：构造小样本 daily_bar，验证快照行数、entry_close 取值、upsert 幂等（重复 snapshot 同日不产生重复行）。
- `track.evaluate.forward_returns`：构造已知后续行情，断言 fwd_h / 超额数值正确；验证 pending 与停牌 flag 逻辑。
- `track.evaluate.scorecard`：构造 score 与 fwd 单调相关的样本，断言 Rank-IC 接近 +1；构造无关样本，断言接近 0。
- `reconstruct`：小区间回放，断言快照日按 every 步长、行数 = 快照数 × top。

## 非目标 / 后续

地基稳定、积累足够样本后，可在其上做：实盘 live IC 反推因子权重的半自动调参（需保持 README 的实证审慎）、(因子特征→前向收益) 数据集的 ML 探索。本设计不涉及。

## 备注

项目当前未启用 git（位于 /Volumes 挂载点），故本 spec 不做 git 提交，仅落地文件。
