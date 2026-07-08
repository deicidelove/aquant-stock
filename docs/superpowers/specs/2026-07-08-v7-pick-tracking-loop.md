# v7 推股闭环 Phase 1：效果看板 + 恢复落库

## 背景
需求分析"推股"核心 = 推荐→跟踪→复盘→优化 闭环。
现状盘点：
- 台账 `picks_log`(780条) + `track/log.snapshot`(落库) + `track/evaluate`(前向收益/超额/Rank-IC，严谨) 已存在。
- **但**：snapshot 未接新 FastAPI 调度 → 落库停在 2026-06-10(近一月停更)；聚合记分卡只输出 markdown、只接旧 Streamlit；新 `/api/assist/scorecard` 只返回原始台账明细，无聚合。

## 目标（补齐闭环缺口）
1. 恢复每日落库：`snapshot()` 接入 EOD 调度。
2. 暴露聚合效果看板：结构化 API + 前端「推荐效果」看板(Top-N 超额/胜率/绝对收益 by T+5/20/60、Live Rank-IC/IR、样本与退市注)。

## 铁律：API/domain 只读；snapshot 是 EOD 任务(读库现算，不触外网)。

## 后端
- `aquant/track/evaluate.py` 新增 `scorecard_data(horizons=HORIZONS, min_names=5) -> dict`：
  - `{sample:{picks,snapshots,start,end,live,replay}, horizons:[{h,settled,pending,mean_excess,win_rate,mean_ret}], rank_ic:[{h,n,mean_ic,ir}], delisted}`。
  - 复用 forward_returns，与 markdown scorecard 同口径(纯读，pending 不计入)。
- API `server/routers/assist.py`：`GET /api/assist/scorecard-summary` → ScorecardSummaryResp。
- 调度 `server/refresh/scheduler.py` EOD：`from aquant.track.log import snapshot; snapshot()`(容错)。

## 前端
- `ScorecardSummary` 组件：样本条 + 超额表(持有期/已结算/pending/平均超额/胜率/绝对收益) + Rank-IC 表 + 退市⚠ + 免责。
- 接入 `AssistReview`(复盘页)顶部；types/client/hook 对齐。

## 拆分
- G1 后端：scorecard_data + API + schema + snapshot 接调度 + 测试。
- G2 前端：types/client/hook + ScorecardSummary + 复盘页接入 + 测试。

## 取舍
- 只做聚合展示 + 恢复落库(闭环跑起来)。"按效果反推因子权重的自动优化"留 Phase 2。
- 数字诚实呈现(超额有正有负)，不美化。
