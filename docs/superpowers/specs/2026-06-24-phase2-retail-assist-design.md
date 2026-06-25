# Phase 2 辅助股民闭环 · 设计文档

- 日期：2026-06-24
- 状态：已确认（待写实现计划）
- 范围：v2 重构总纲的「板块② 辅助股民」。一个子系统，分后端/前端两期实现。
- 上游：[v2 重构总纲](2026-06-23-stock-system-v2-redesign.md)；Phase 1A 后端地基 + Phase 1B 前端驾驶舱已合并。

## 目标

把散落的"选股/决策/个股/推荐跟踪"按用户目的串成一个闭环，并补上唯一缺失的部件「我的持仓」：

```
选票 → 买卖时机 → 我的持仓(记账+盈亏) → 复盘 → 再选
 │        │            │                  │
建仓名单  个股决策     录入真实买卖        推荐记分卡
+研报速览 买卖点/止损   持仓浮盈亏          +持仓盈亏汇总
         (复用1A报告)  +卖出提醒
```

## 关键决策（已与用户确认）

| 维度 | 决策 |
|---|---|
| 我的持仓性质 | 手动真实交易记账（用户录入真实买/卖；与模拟盘 paper account 独立） |
| 复盘/优化深度 | 纯展示复盘数据（推荐记分卡 + 持仓盈亏汇总），不做自动调参（YAGNI） |
| 复用 | 选票=`daily_picks`/`briefing`；买卖时机=`decision`(1A `/api/stock/{code}/report`)；复盘=`track` 记分卡 |

## 架构铁律（沿用 v2 总纲）

写交易经 `POST` 落本地 DuckDB；读取一律只读库或复用领域函数；API 请求处理内无第三方联网。

## 第 1 节 · 后端（Plan 2A）

### 新增表 `trades`（手动交易流水）

字段：`tid`(自增/唯一)、`date`、`code`、`side`(buy/sell)、`shares`、`price`、`note`。
在 `aquant/data/store.py` 的 `TABLE_KEYS` 注册主键 `["tid"]`。

### 持仓聚合服务（纯函数，从 trades 计算）

- **当前持仓**：按 code 聚合买卖流水 → 持股数、加权平均成本；持股数 > 0 视为在仓。用最新价（优先 `quote_snapshot` 盘中、回退 `daily_bar` 最新收盘）算市值与浮动盈亏（金额 + 百分比）。
- **已实现盈亏**：卖出按加权成本结转，累计已实现盈亏。
- **卖出提醒**：对每个在仓标的调用 `research.decision`/`_levels` 的关键价位与 `timing` 的最新动作，产出标记集合：`跌破止损`（现价 ≤ stop）、`到压力位`（现价 ≥ resistance）、`信号转空`（择时 latest_action=卖出/空仓）。无触发则空。

### 新端点

| 方法 路径 | 作用 |
|---|---|
| `POST /api/holdings/trade` | 记一笔买/卖（body: date,code,side,shares,price,note?）→ 返回写入的 tid |
| `GET /api/holdings/trades` | 交易流水列表 |
| `DELETE /api/holdings/trade/{tid}` | 删除一笔（纠错） |
| `GET /api/holdings` | 当前持仓 + 浮动盈亏 + 每只卖出提醒 |
| `GET /api/holdings/pnl` | 盈亏汇总（已实现 + 未实现 + 合计） |
| `GET /api/assist/scorecard` | 推荐记分卡结构化（基于 `track.forward_returns`/`scorecard`） |
| `GET /api/assist/briefing?top=N` | 研报速览表结构化（基于 `research.briefing`） |

服务层放 `aquant/`（领域纯函数，如 `aquant/portfolio/holdings.py`）便于单测；FastAPI 路由薄封装。`trades` 写入是该子系统唯一的写操作。

## 第 2 节 · 前端（Plan 2B）

新增"辅助股民"板块（顶部导航入口 + 路由前缀，如 `/assist`），4 个页面：

- **选票** `/assist/picks`：每日建仓名单（Top-N）+ 研报速览表（多维决策速览）。
- **个股决策** `/assist/stock/:code`：复用 Phase 1B 的 `StockDetail`（K 线 + 研判 + 买卖点/止损）。
- **我的持仓** `/assist/holdings`：交易录入表单（日期/代码/方向/数量/价格）→ 提交后刷新；持仓表（代码/名称/持股/成本/现价/浮盈亏/🔴卖出提醒）；交易流水列表（可删错记）。
- **复盘** `/assist/review`：推荐记分卡（命中率/超额/Rank-IC，多 horizon）+ 持仓盈亏汇总（已实现/未实现/合计）。

沿用 1B 架构：纯展示组件（props in）+ TanStack Query hooks（持仓相关用 mutation + invalidate 刷新）+ 既有 API client 扩展。

## 第 3 节 · 分期

- **Plan 2A 后端**：`trades` 表 + 持仓聚合服务（含卖出提醒）+ holdings/assist 端点；pytest（临时库 + 注入交易，验证聚合/盈亏/提醒/CRUD）。
- **Plan 2B 前端**：辅助股民板块 4 页面 + 录入 mutation；Vitest + Testing Library。

## 非目标（YAGNI）

- 不做自动调参 / 因子权重建议（复盘只展示数据）。
- 不接实盘下单 / 券商 API。
- 不做多账户、不做融资融券/期权；持仓限单账户、A 股、手动记账。
- 不与模拟盘 paper account 混用（二者独立；模拟盘属 Phase 3 量化）。

## 未决 / 计划阶段再定

- `trades` 自增 tid 的实现方式（DuckDB sequence vs max+1）。
- 卖出提醒触发阈值的细节（是否给"临近止损 3%"这类软提醒）。
- 研报速览 `briefing` 在真实全市场下的耗时（必要时限制候选池或缓存）。
