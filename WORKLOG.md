# stock 工作日志

> 倒序记录（最新在上）。每个条目包含：问题 / 已完成 / 待完成 / 下一步 / 关键决策。
> 用法：让 Claude 「记录进度」/「看进度」/「总结进度」。
> 此文件**不进 memory 系统**，纯项目级记录。

---

## 2026-07-08 v7 推股闭环 Phase1：效果看板 + 恢复落库

**背景**：需求"推股"闭环=推荐→跟踪→复盘→优化。发现 `track/log(落库)`+`track/evaluate(前向收益/超额/Rank-IC)` 已存在但①snapshot 未接新调度(落库停在2026-06-10)②聚合记分卡只输出markdown、只接旧Streamlit，新API只返回原始台账。

**已完成**：
- `evaluate.scorecard_data`：结构化聚合(样本/各持有期超额·胜率·绝对收益/Live Rank-IC·IR/退市)，与markdown同口径纯读。
- API `/api/assist/scorecard-summary`；`snapshot()` 接回 EOD 调度恢复每日落库。
- 前端 `ScorecardSummary`(超额表+Rank-IC表+退市注)接入复盘页顶部。
- 后端+4(122)、前端+2(110)全绿+build+e2e。真实：780条/26快照 T+60平均超额+2.92%胜率44.7%(诚实呈现)。

**推股闭环 Phase2(留后续)**：按效果反推因子权重自动优化。
**其他候选**：持仓VaR/CVaR优化 / Qlib因子 / 腾讯快照兜底。

---

## 2026-07-08 v6 数据层 Phase2：融资融券 + 大宗（驾驶舱）

**已完成**：
- source `margin_sse(区间)`/`margin_szse(按日汇总)`/`block_trade_stat`；store `margin_balance[date,market]`/`block_trade[date]`；refresh 挂 EOD(sz 失败不影响 sh)。
- `board.margin_summary`(两市融资余额合计+趋势,折算亿) + `block_trade_recent`(**自算**溢价占比,原始"占比"字段单位不一致不可信)。
- API `/api/cockpit/margin`+`/block-trade`；驾驶舱加 MarginPanel(余额+迷你趋势线) + BlockTradePanel(折溢价)。
- 后端+12(118)、前端+4(108)全绿+build+e2e。真实：两市融资余额14882亿。

**数据层进度**：涨停梯队/北向(v5) + 融资融券/大宗(v6) 已入驾驶舱。腾讯主源可靠性兜底(已验证代理下可用)与 mootdx/Level2 留后续。

**下一步候选**：腾讯快照兜底(可靠性) / 转板块：推股闭环 / 持仓VaR优化 / Qlib因子。

---

## 2026-07-08 v5 数据层升级 Phase1：涨停梯队 + 北向（驾驶舱）

**背景**：调研 a-stock-data(40端点/13源) 后定数据层为地基。Phase1 选 akshare 零新依赖可得的两块。

**已完成**：
- source `limit_pool(涨停池:连板/封板资金/炸板/行业)` + `north_summary(北向)`；store `limit_pool[code,date]`/`north_flow[date,market]`；refresh 挂盘中 job。
- `aquant/board.py`：`limit_ladder`(连板梯队/封板率/炸板率/涨停家数/行业分布) + `north_flow`，只读。
- API `/api/cockpit/limit-ladder` + `/north-flow`；驾驶舱加 LimitLadderPanel(阶梯柱+情绪 Stat+行业标签) + NorthFlowPanel。
- 后端+11(106)、前端+6(104)全绿+build+e2e。真实：今日23家涨停最高7板(恒尚节能)封板率0.652。
- 口径诚实：北向实时分钟2024-08停发，沪深股通取0，前端注明。

**下一步(数据层后续Phase / 或转其他板块)**：mootdx/腾讯主源可靠性迁移、融资融券/大宗/Level2；或按需求分析做 推股闭环 / 持仓优化 / 量化因子。

## 2026-07-06 v4 AI 多智能体投研报告 ✅ 完成

**已交付**：
- D1 后端(main 9054360)：`llm.chat` provider(Ollama优先urllib零依赖→claude-p→None)；`aquant/analysts.py:ai_research`(4分析师技术/资金含龙虎榜/消息含大盘情绪/基本面 + 多空辩论；规则给硬决策，LLM给叙事，无LLM规则降级)；`research_report`缓存表+读写；job kind `ai_research`+`POST/GET /api/stock/{code}/ai-report`(异步生成+只读缓存守离线铁律)。后端+10=95。
- D2 前端：`AiReport`组件(生成→轮询→4分析师卡片+多空辩论红多绿空+结论徽章+仓位+风险+免责)接入StockDetail；前端+5=100。
- 真实端到端：茅台报告4分析师视角各异、多空辩论有交锋，质量佳。claude-p串行6调用较慢(>45s)，Ollama可提速。

**待用户定**：是否装 Ollama(brew install ollama + qwen2.5:7b ~5GB)以本地提速/离线。设 `AQUANT_OLLAMA_MODEL=qwen2.5:7b` 即自动启用。

**历史记录（原暂停条目，已完成）**：

**背景**：调研五个高星投研项目(TradingAgents ~80k / ai-hedge-fund ~59k / Vibe-Trading / Vibe-Research / Qlib)，结论=LLM多智能体投研是主流；aquant 数据底子(全A股+龙虎榜+消息面)更懂A股，缺的就是这层。

**已定方向(用户确认)**：AI多智能体投研报告；LLM 走**本地 Ollama 优先** → 回退 `claude -p`(免key,已验证可用) → 规则降级。铁律：LLM异步生成+缓存，请求路径只读。

**进度**：
- spec `docs/superpowers/specs/2026-07-06-v4-ai-research-agents.md` 完成。
- 分支 `v4a-ai-research-backend`(从 main 8fe8e00)；D1-T1 `test_llm_provider.py` 已写(chat: Ollama优先/claude回退/降级)，**实现未写**。
- 本机现状：claude CLI 可用；**Ollama 未装**(brew 可用、105G 空间)，装 Ollama 需用户点头(约5GB qwen2.5:7b)，另行确认。

**下一步(恢复时)**：
1. 实现 `llm.chat` provider(Ollama urllib + claude 回退) → T1 绿。
2. D1-T2 `aquant/analysts.py: ai_research`(4分析师+PM综合+多空辩论, mock chat 测试, 规则降级)。
3. D1-T3 `research_report` 缓存表+读写；T4 job注册+`POST/GET /api/stock/{code}/ai-report`。
4. D1 合并 main；D2 前端 AI报告区块(生成/轮询)。
计划见 todo；jobs runner(`quant/jobs.py`) + `research_cache.py` 模式可复用。

---

## 2026-07-05 v3.4 市场消息面 / 新闻情绪（资深股民三块最后一块）

**已完成**：
- 后端 `aquant/sentiment.py`：关键词法 `score_text`(利好+1/利空-1/中性0，宏观+个股词典)、`aggregate`(0-100 情绪指数+分档标签)、`market_news_sentiment`(读 market_news 表聚合，只读)。
- source `news.market_news` 包 `stock_info_global_em`(全球财经快讯 标题/摘要/时间/链接)；store `market_news` 表键；`refresh_market_news` 抓+打分入库，挂盘中 job。
- API `/api/cockpit/news-sentiment` + schema。
- 前端 `NewsSentiment` 组件(情绪指数+利好/利空/中性计数+快讯列表，利好红/利空绿色点，紧凑/完整两态)；看板底部紧凑版、驾驶舱完整版。
- 后端+8(85)、前端+12(98)全绿+build+e2e。真实冒烟：50 条快讯打分入库。

**资深股民三块(K线专业化 / 龙虎榜 / 消息面)全部完成。**

---

## 2026-07-05 v3.3A 龙虎榜后端（游资/机构席位）

**已完成**：
- 域层 `aquant/lhb.py`：`classify_seat`（机构专用/股通→北向/知名游资词典 HOTMONEY/普通）、`lhb_today(limit)`（最近上榜日按净买额降序+标签）、`lhb_stock(code,date)`（买卖前五席位穿透）。只读 DuckDB，请求路径不发网络。
- source `akshare_source.lhb_seats(code,date,flag)` 包 `stock_lhb_stock_detail_em`，@_robust。
- store 新表键 `lhb_seat:[code,date,side,seat]`。
- refresh `server/refresh/lhb.py:refresh_lhb(days)`：抓上榜列表+逐只买卖席位入库，挂 EOD job。真实数据 reason 可空→填 ""（reason 是主键）。
- API `/api/lhb/today`、`/api/lhb/stock/{code}`（router+schemas，app 注册）。
- 测试 +13（77 passed）。真实入库冒烟：东山精密净买11.3亿(机构+北向)、横店东磁命中佛山无影脚游资。

**下一步**：v3.3B 前端（龙虎榜页 + 席位穿透 + 导航 + StockDetail 追加）。

---

## 2026-07-05 17:05 — v3 自选股看板上线(产品转向散户日常看盘)
**问题**：v2/v2.1被判失败产品(量化口径,散户看不懂)。调研后转向:以自选/持仓为中心的日常看盘。
**已完成**：v3A后端(watchlist表+CRUD+board自选∪持仓卡片+/api/board)、board性能修复(43s→4.8s,复用物化评分)、v3B前端(看板设新首页/=Board:大盘条+加自选+卡片[信号/迷你走势/买点止损/提醒],宏观驾驶舱移/macro,量化/复盘收进导航'高级')。全合并推送 main 201fbd1,后端55+前端75测试绿,终审均Ready to merge。
**待完成**：v3 主体完成。可选后续。
**下一步**：无强制项。可选:①今日热点屏(涨停/龙虎榜/板块资金);②board自选多时批量优化;③清理死代码(useWatchlist未用/孤儿OverviewPanel等);④sentiment阈值/news预取;⑤起项目实测看板真实观感。
**关键决策**：目标用户=普通股民(含开发者本人)日常看盘;驾驶舱/量化降级为'高级';board数据即时算自daily_bar(不会空);性能靠物化factor_score。


## 2026-07-05 11:19 — v2.1 全部完成（宏观驾驶舱+深色主题上线）
**问题**：v2.1 前端(深色+宏观驾驶舱)收尾。
**已完成**：v2.1A后端(9dfdad5) + v2.1B前端(20fd618)全部合并推送。驾驶舱重做成宏观盘面(指数/情绪/大盘资金/板块资金/异常资金)、深色主题、选股迁选票。前端65+后端51测试绿。冒烟真实数据: 沪深300 4801.81/情绪37.1偏冷/大盘资金-434.6亿; 板块资金&异常资金端点通但暂空(sector_fund_flow待盘中刷新入库、异常待历史积累)。终审 opus Ready to merge。
**待完成**：v2.1 主体完成。可选后续见下。
**下一步**：无强制项。可选:①让板块资金/异常资金出数(盘中跑刷新或手动 ingest sector_fund_flow+积累fund_flow历史);②清理孤儿组件(OverviewPanel/SectorPanel/useOverview/useSectors)+未接线SignalTag;③选票one_liner决策卡(需后端enrich picks);④EChart[option]每渲重建优化。
**关键决策**：market-fund后端已/1e8返亿元前端直显; 深色为className替换不动结构; 红涨绿跌保留。


## 2026-07-04 22:39 — v2.1A 驾驶舱宏观后端完成；下一步 v2.1B 前端
**问题**：驾驶舱要从选股列表重做成宏观盘面；v2.1A 做后端。
**已完成**：v2.1A 后端 5 任务全过并合并推送（main 9dfdad5，51测试绿）。行业资金流源+表+刷新、个股资金盘中刷新+调度、aquant/macro.py(情绪/大盘资金/多指数/板块资金/异常资金z-score)、5个/api/cockpit宏观端点。终审 opus Ready to merge。
**待完成**：v2.1B 前端——尚未写 spec-plan、未实现。
**下一步**：写 Plan v2.1B 前端（深色量化驾驶舱主题+UI原子 + 驾驶舱重构为宏观五模块[消费新端点/更新于/实时标记] + 建仓名单&高分股迁到'辅助股民·选票'并加厚成决策卡）。开工先 writing-plans。
**关键决策**：驾驶舱=纯宏观(指数/情绪/大盘资金/板块资金/异常资金)，选股移到选票；北向剔除；异常资金用z-score(越跑历史越准)。


## 2026-06-29 23:42 — v2 三板块上线；下一步做 v2.1 体验升级（设计待拍板）
**问题**：v2（FastAPI+React 三板块）已上线，但真实联调后用户反馈驾驶舱"信息单薄、对股民没用、不好看、内容大多是死的（盘中数据不跳动）"。
**已完成**：v2 全部完成并推 GitHub（main `6c02c25`，前端48+后端38测试绿）。地基(FastAPI只读库+后台刷新+物化评分) + 板块①驾驶舱(1A/1B) + ②辅助股民(2A/2B) + ③量化(3A/3B 异步回测+因子IC)。设计/计划在 docs/superpowers/。
**待完成**：v2.1 体验升级——尚未落盘 spec、未实现。设计已讨论但用户**还没最终拍板**。
**下一步**：确认 v2.1 三支柱设计 → 落盘 spec(docs/superpowers/specs) → 写 Plan A(后端)+Plan B(前端) → 执行。开工先问用户"设计OK还是要改"。
**关键决策**：v2.1 三根支柱——①动作为纲(首页改"今日行动板"：风向条+持仓提醒+带理由的建仓名单，结论在上可下钻)；②深色量化驾驶舱主题+信息加厚(把后端 decision 已有的 signal/一句话理由/作战计划买点止损目标/风险 端到列表，告别裸表格)；③让驾驶舱"活起来"(盘中数据改读 quote_snapshot/sector_snapshot 实时算涨跌家数/指数/资金，标"更新于HH:MM"，盘中轮询见跳动；区分盘中实时/收盘定)。根因：overview 读 daily_bar 昨收=静态，故轮询也不动。遗留小项：EChart [option]每渲重建优化、cosmetic(分数格式化/平盘中性色/行键盘可达)。
