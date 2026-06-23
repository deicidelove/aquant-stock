"""推荐跟踪台账：每日推荐落库 → 事后算前向收益 → live 记分卡。

- log:      snapshot() 当日推荐入库；reconstruct() 历史回放冷启动。
- evaluate: forward_returns() / scorecard()，无状态只读，把台账 join 行情算出
            前向收益、超额、live Rank-IC，与 README 回测 IC 对照。

只搭地基（结构化留痕 + 评估），不含自动调参/ML。
"""
from __future__ import annotations

from .log import reconstruct, snapshot
from .evaluate import forward_returns, scorecard

__all__ = ["snapshot", "reconstruct", "forward_returns", "scorecard"]
