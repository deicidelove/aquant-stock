# v6 数据层升级 Phase 2：融资融券 + 大宗交易

## 背景
数据层 Phase 2。选 akshare 零新依赖、驾驶舱资金面直接受益的两块。
(腾讯主源可靠性兜底已验证可用[代理下 qt.gtimg.cn 通]，作后续单独增量，避免大改在跑的快照管线。)

## 数据(已验证)
- `stock_margin_sse(start,end)` → 上交所融资融券(区间多天)：信用交易日期/融资余额/融资融券余额…
- `stock_margin_szse(date)` → 深交所(按日)：融资余额/融资融券余额…
- `stock_dzjy_sctj()` → 大宗交易每日统计(全市场)：交易日期/大宗成交总额/溢价成交总额/折价成交总额/占比。

## 目标
1. 融资融券：两市融资余额(杠杆资金情绪)+ 趋势。
2. 大宗交易：近期折溢价成交(资金动向信号)。
3. 驾驶舱资金面加两面板。

## 铁律：API/domain 只读 DuckDB；仅 refresh 发网络。

## 数据模型
- `margin_balance` 键 `[date, market]`：date, market('sh'/'sz'), fin_balance(融资余额), total_balance(融资融券余额)。
- `block_trade` 键 `[date]`：date, total_amount(成交总额), premium_amount(溢价), discount_amount(折价), premium_ratio(溢价占比)。

## 域层 `aquant/board.py`（扩展）
- `margin_summary(days=20) -> {date, sh, sz, total_fin, total_bal, series:[{date, total_fin}]}`
  - series 按日汇总各市场 fin_balance(单位亿)；缺市场按可得口径合计，note 标注。
- `block_trade_recent(days=10) -> {rows:[{date, total_amount, premium_ratio}]}`(单位亿)。
- 无数据返回空结构不报错。

## refresh `server/refresh/board_data.py`（扩展）
- `refresh_margin()`：SSE 取近 ~10 交易日区间(一次) save sh；SZSE 取最新日 save sz。
- `refresh_block_trade()`：抓统计取近日 save。
- 挂 EOD job（日度数据，收盘后更新）。

## API（cockpit router）
- `GET /api/cockpit/margin?days=20` → MarginResp
- `GET /api/cockpit/block-trade?days=10` → BlockTradeResp

## 前端
- `MarginPanel`：两市融资余额合计(亿)+ 融资余额趋势迷你线；`BlockTradePanel`：近日大宗折溢价。
- 驾驶舱资金面接入；types/client/hooks 对齐。

## 拆分
- F1 后端：source(3) + store 键(2) + 域层(2) + refresh(2) + API + schemas + 测试(mock)。
- F2 前端：types/client/hooks + 两面板 + 驾驶舱接入 + 测试。

## 取舍
- 融资余额单位大(万亿)，域层折算亿；两市口径可能不同步日，按可得日合计并注明。
- 大宗只做全市场统计(个股大宗留后续)。
