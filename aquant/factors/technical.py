"""技术 / 动量 / 量价类因子。

每个因子接收单只股票日线 DataFrame（按日期升序），返回与之对齐的 pd.Series。
导入本模块即完成注册（见 registry）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .registry import register


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


@register("mom_20", "20日动量（收益率）", direction=1)
def mom_20(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(20)


@register("mom_60", "60日动量（收益率）", direction=1)
def mom_60(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(60)


@register("ma_bias_20", "20日乖离率（价格相对MA20偏离）", direction=-1)
def ma_bias_20(df: pd.DataFrame) -> pd.Series:
    ma = df["close"].rolling(20).mean()
    return (df["close"] - ma) / ma


@register("trend_align", "多头排列强度（MA5>MA20>MA60 的有序程度）", direction=1)
def trend_align(df: pd.DataFrame) -> pd.Series:
    c = df["close"]
    ma5, ma20, ma60 = c.rolling(5).mean(), c.rolling(20).mean(), c.rolling(60).mean()
    # 三线相对间距，正值代表多头排列
    return ((ma5 - ma20) / ma20 + (ma20 - ma60) / ma60) / 2


@register("rsi_14", "14日RSI（相对强弱）", direction=1)
def rsi_14(df: pd.DataFrame) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


@register("vol_ratio_5_20", "量比（5日均量/20日均量）", direction=1)
def vol_ratio_5_20(df: pd.DataFrame) -> pd.Series:
    v5 = df["volume"].rolling(5).mean()
    v20 = df["volume"].rolling(20).mean()
    return v5 / v20.replace(0, np.nan)


@register("volatility_20", "20日收益波动率", direction=-1)
def volatility_20(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change().rolling(20).std()


@register("turnover_mean_20", "20日平均换手率（活跃度）", direction=1)
def turnover_mean_20(df: pd.DataFrame) -> pd.Series:
    if "turnover" not in df.columns:
        return pd.Series(np.nan, index=df.index)
    return df["turnover"].rolling(20).mean()


@register("macd_hist", "MACD柱（DIF-DEA）", direction=1)
def macd_hist(df: pd.DataFrame) -> pd.Series:
    dif = _ema(df["close"], 12) - _ema(df["close"], 26)
    dea = _ema(dif, 9)
    return (dif - dea) * 2
