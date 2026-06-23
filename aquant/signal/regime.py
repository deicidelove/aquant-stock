"""大盘 regime（市场状态）择时过滤。

用宽基指数趋势作为「总开关」：指数在长期均线之上=risk-on（允许持仓），
跌破=risk-off（空仓避险），用于压低组合在系统性熊市中的回撤。

regime 信号只用截至当日的指数信息，无未来函数；回测时由引擎再 shift 一日生效。
"""
from __future__ import annotations

import pandas as pd

from ..data import store


def index_close(index_code: str = "sh000300") -> pd.Series:
    """从仓库读指数收盘价，index=date(str)，升序。"""
    df = store.query("SELECT date, close FROM index_daily WHERE code = ? ORDER BY date",
                     [index_code])
    return df.set_index("date")["close"] if not df.empty else pd.Series(dtype=float)


def trend_regime(close: pd.Series, ma: int = 200) -> pd.Series:
    """指数 > MA(ma) → 1（risk-on），否则 0（risk-off/空仓）。"""
    return (close > close.rolling(ma).mean()).astype(float)


def regime_series(index_code: str = "sh000300", ma: int = 200) -> pd.Series:
    """便捷：直接得到某指数的 regime 信号（index=date）。"""
    return trend_regime(index_close(index_code), ma=ma)
