"""因子注册表。

因子 = 一个把单只股票日线 DataFrame 映射为一列因子值（Series，与日期对齐）的函数。
用装饰器登记，选股/回测层按名字取用，便于统一管理与扩展。

约定：输入 df 含列 [date, open, high, low, close, volume, amount, ...]，按日期升序。
输出 pd.Series（index 与 df 对齐），越大代表越“看多/越强”。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

FactorFn = Callable[[pd.DataFrame], pd.Series]


@dataclass
class Factor:
    name: str
    fn: FactorFn
    desc: str
    direction: int = 1  # 1=越大越好，-1=越小越好（打分时统一乘以方向）


_REGISTRY: dict[str, Factor] = {}


def register(name: str, desc: str = "", direction: int = 1):
    def deco(fn: FactorFn) -> FactorFn:
        if name in _REGISTRY:
            raise ValueError(f"因子重名: {name}")
        _REGISTRY[name] = Factor(name=name, fn=fn, desc=desc, direction=direction)
        return fn
    return deco


def get(name: str) -> Factor:
    if name not in _REGISTRY:
        raise KeyError(f"未注册因子: {name}（已有: {list(_REGISTRY)})")
    return _REGISTRY[name]


def all_factors() -> dict[str, Factor]:
    return dict(_REGISTRY)


def compute(df: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """对单只股票计算多个因子，返回 [date, <factor>...] 的 DataFrame。"""
    out = pd.DataFrame({"date": df["date"].values})
    for n in names:
        out[n] = get(n).fn(df).values
    return out
