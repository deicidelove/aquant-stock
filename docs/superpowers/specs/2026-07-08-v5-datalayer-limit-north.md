# v5 数据层升级 Phase 1：涨停梯队 + 北向资金

## 背景
需求调研(参考 a-stock-data)后定：数据层是各板块"实时资金/情绪/异常"的地基。
Phase 1 选**驾驶舱最刚需、且 akshare 零新依赖可得**的两块：涨停梯队、北向。
(mootdx/腾讯 主源可靠性迁移、融资融券/大宗/Level2 留后续 Phase。)

## 数据(已验证 akshare 可得)
- `stock_zt_pool_em(date)` → 涨停池：代码/名称/涨跌幅/成交额/换手率/**封板资金/炸板次数/连板数/所属行业/首次封板时间**。
- `stock_hsgt_fund_flow_summary_em()` → 北向汇总：沪股通/深股通/港股通 资金净流入。
  - **注**：交易所 2024-08 起停发北向实时分钟流向，沪深股通实时净额常为 0；如实降级，取可得值，不虚构。

## 目标
1. 涨停梯队：连板高度分布(1板/2板/3板+/最高板)、封板率、炸板率、涨停家数、行业分布 → A股情绪核心指标。
2. 北向资金：当日净流入(可得范围)，作辅助资金面板。
3. 驾驶舱新增两个面板呈现。

## 铁律
- API/domain 只读 DuckDB；仅 refresh 任务发网络(盘中+EOD 抓涨停池/北向入库)。

## 数据模型(DuckDB)
- `limit_pool` 键 `[code, date]`：code,name,date,pct_chg,amount,turnover,seal_fund(封板资金),break_times(炸板次数),boards(连板数),industry,first_seal_time。
- `north_flow` 键 `[date, market]`：date,market(沪股通/深股通/港股通沪/港股通深),net(资金净流入,亿)。

## 域层 `aquant/board.py`（新，避免与现有 macro 混）
- `limit_ladder(date=None) -> {date, limit_up_count, seal_rate, break_rate, max_boards, ladder:[{boards,count,names:[...]}], by_industry:[{industry,count}]}`
  - date 缺省取 limit_pool 最新日；seal_rate/break_rate 由炸板次数聚合估算；ladder 按连板数分组降序。
- `north_flow(date=None) -> {date, rows:[{market,net}]}`。
- 只读、无网络、无数据返回空结构不报错。

## refresh `server/refresh/board_data.py`
- `refresh_limit_pool()`：抓当日涨停池 save；`refresh_north()`：抓北向 save。
- 挂 intraday job(盘中滚动)+ EOD。

## API（cockpit router, prefix /api/cockpit）
- `GET /api/cockpit/limit-ladder?date=` → LimitLadderResp
- `GET /api/cockpit/north-flow?date=` → NorthFlowResp

## 前端
- 驾驶舱新增：
  - `LimitLadderPanel`：连板高度分布(柱/阶梯)、封板率/炸板率/涨停家数(Stat)、最高板龙头、行业分布 top。
  - `NorthFlowPanel`：北向各通道净流入(红绿)。
- types/client/hooks 对齐。

## 拆分
- E1 后端：source(2) + store 键(2) + board 域层 + refresh + API + schemas + 测试(mock source)。
- E2 前端：types/client/hooks + 两面板 + 驾驶舱接入 + 测试。

## 取舍
- 北向实时分钟已停发 → 只做日度/可得值，不假装实时。涨停梯队是更可靠、更核心的情绪信号，作 Phase 1 旗舰。
- 封板率/炸板率用涨停池现有字段估算(封住=炸板次数当日已回封的近似)，标注口径。
