# v4 AI 多智能体投研报告

## 背景
调研五个高星投研项目（TradingAgents ~80k / ai-hedge-fund ~59k / Vibe-Trading / Vibe-Research / Qlib）后，
最大公约数 = **LLM 多智能体投研**：多角色分析师 + 多空辩论 → 可解释的研判报告。
aquant 已有全 A 股数据 + 龙虎榜(游资) + 消息面情绪，喂给 agent 的"料"比参考项目更懂 A 股，是差异化护城河。
aquant 当前"研判"是规则化单一结论，缺的正是这一层。

## 目标
把已建好的 K线/技术/因子/资金/龙虎榜/消息面/基本面 **综合成一份多智能体投研报告**：
- 4 位分析师各出观点：技术面 / 资金面(含龙虎榜) / 消息面(含大盘情绪) / 基本面。
- 组合经理综合：多空辩论(bull/bear) + 明确操作倾向(买入/观望/回避) + 理由 + 风险 + 仓位建议。
- LLM 走**本地 Ollama 优先**，回退已可用的 `claude -p`(免key)，再回退**规则降级**(始终有结果)。

## LLM 决策(用户已定)
- 首选 **本地 Ollama**(完全离线、免key、隐私)；本机暂未装，安装后自动启用。
- provider 无关：`llm.chat(prompt)` 依次尝试 Ollama → claude -p → None。
- 铁律：LLM 调用是网络 → **仅异步任务**发起(生成报告)；请求路径只读缓存(offline)。

## 域层 `aquant/analysts.py`
- `ai_research(code, offline=True, chat=None) -> dict`：
  - `rep = research.stock_report(code, offline=offline)`；补 `lhb.lhb_stock(code)`、`sentiment.market_news_sentiment()`。
  - 4 分析师：各用结构化事实拼 prompt → `chat()` → 1-2 句观点(chat 返 None 则规则文本降级)。
  - 组合经理：4 观点 + 事实 → `chat()` → {bull, bear, stance, reason, position, risks}(降级用现有 decision/one_liner 规则)。
  - 返回 `{code,name,as_of,analysts:{technical,capital,news,fundamental},debate:{bull,bear},verdict:{stance,reason,position,risks},llm_used:bool}`。
  - 无论 LLM 是否可用都返回完整结构。

## provider `aquant/llm.py`（重构，保持 synthesize 兼容）
- `chat(prompt, timeout=120) -> str|None`：
  - Ollama：若 `AQUANT_OLLAMA_MODEL` 已设且 127.0.0.1:11434 可达 → POST /api/generate(stream=false)，取 response。用 stdlib urllib，零新依赖。
  - 否则 `claude -p`(现有 _ask)。
  - 否则 None。
- `available()` 保留。

## 存储 `research_report` 表 [code, as_of]，列 report_json
- `research_cache.save_report / read_report`。
- store TABLE_KEYS 增 `research_report`。

## 异步任务 + API（stock router）
- 注册 job kind `ai_research`：runner 调 `ai_research(code, offline=False)`(实网 LLM) → 存缓存。
- `POST /api/stock/{code}/ai-report` → submit_job → {job_id}。
- `GET /api/stock/{code}/ai-report` → 读缓存(offline) → {report: <dict|null>}。
- 前端轮询 GET 直到 report 非空(不依赖额外 job 端点)。

## 前端
- StockDetail 加「🧠 AI 投研报告」区块：无缓存显示"生成"按钮(POST)→轮询→展示。
- 展示：4 分析师卡片 + 多空辩论(红多/绿空双列) + 综合结论(操作倾向徽章+理由+仓位+风险)。
- 标注"仅供研究，不构成投资建议"。
- types/client/hooks 对齐。

## 拆分
- D1 后端：llm.chat provider + analysts.ai_research + 缓存表/读写 + job + API + 测试(mock chat)。
- D2 前端：AI 报告区块 + 生成/轮询 + types/client/hooks + 测试。

## 取舍
- 每次生成 5 次 LLM 调用(4 分析师+1 PM)，异步可接受；Ollama 慢但离线。
- 规则降级保证没装 LLM 也能用(结构同、llm_used=false)。
- 测试全程 mock chat，不依赖真实 LLM/网络。
- 安装 Ollama 是用户机器上的动作，另行确认；不阻塞后端开发。
