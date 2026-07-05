# stock 工作日志

> 倒序记录（最新在上）。每个条目包含：问题 / 已完成 / 待完成 / 下一步 / 关键决策。
> 用法：让 Claude 「记录进度」/「看进度」/「总结进度」。
> 此文件**不进 memory 系统**，纯项目级记录。

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
