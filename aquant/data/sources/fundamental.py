"""基本面 / 筹码 数据源（投研维度）。

- valuation_snapshot(): 全市场估值快照（PE/PB/总市值/流通市值/换手/量比），一次调用。
- chip_distribution(code): 筹码分布（获利比例/平均成本/90集中度）。
- financial_abstract(code): 关键财务指标（营收/净利/ROE/毛利）+ 同比增速。
- dividend(code): 最近分红。

东财接口复用 akshare_source 的交替代理强重试（_robust）。深度财务按需 per-stock 取，
不做全市场 bulk（5000 只逐只财报太重）。
"""
from __future__ import annotations

import akshare as ak
import pandas as pd

from .akshare_source import _robust

# ---------------------------------------------------------------- 估值（全市场快照）

_VAL_MAP = {
    "代码": "code", "名称": "name", "最新价": "close", "涨跌幅": "pct_chg",
    "换手率": "turnover", "量比": "volume_ratio", "市盈率-动态": "pe",
    "市净率": "pb", "总市值": "total_mv", "流通市值": "circ_mv",
    "60日涨跌幅": "chg_60d", "年初至今涨跌幅": "chg_ytd",
}


@_robust
def valuation_snapshot() -> pd.DataFrame:
    """全市场估值快照（直连东财 clist，单请求大 pz 一次拉全 A，避免分页爬取断流）。

    东财字段：f2最新价 f3涨跌幅 f8换手率 f9市盈率动 f10量比 f12代码 f14名称
    f20总市值 f21流通市值 f23市净率。
    """
    import requests
    params = {
        "pn": "1", "pz": "6000", "po": "1", "np": "1", "fltt": "2", "invt": "2",
        "fid": "f3", "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:7,m:1+t:3",
        "fields": "f12,f14,f2,f3,f8,f9,f10,f20,f21,f23",
    }
    r = requests.get("https://push2.eastmoney.com/api/qt/clist/get",
                     params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    data = r.json()["data"]["diff"]
    df = pd.DataFrame(data).rename(columns={
        "f12": "code", "f14": "name", "f2": "close", "f3": "pct_chg", "f8": "turnover",
        "f9": "pe", "f10": "volume_ratio", "f20": "total_mv", "f21": "circ_mv", "f23": "pb"})
    df["code"] = df["code"].astype(str).str.zfill(6)
    for c in df.columns:
        if c not in ("code", "name"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["code", "name", "close", "pct_chg", "turnover", "pe", "pb",
               "total_mv", "circ_mv", "volume_ratio"]]


# ---------------------------------------------------------------- 筹码分布

# 筹码走东财 push2his，断流时整批重试会拖满 ~27s；此维度可降级（取不到不影响决策），
# 故调小重试快速失败：proxy/直连各试一次即放弃。
@_robust(attempts=2, max_wait=1.0)
def chip_distribution(code: str) -> dict:
    """最新筹码分布：获利比例 / 平均成本 / 90集中度。"""
    df = ak.stock_cyq_em(symbol=code, adjust="qfq")
    if df is None or df.empty:
        return {}
    r = df.iloc[-1]
    g = lambda k: float(r[k]) if k in r and pd.notna(r[k]) else None
    return {
        "date": str(r.get("日期", "")),
        "profit_ratio": g("获利比例"),       # 获利盘占比
        "avg_cost": g("平均成本"),
        "concentration_90": g("90集中度"),
        "cost_90_low": g("90成本-低"),
        "cost_90_high": g("90成本-高"),
    }


# ---------------------------------------------------------------- 关键财务指标

# stock_financial_abstract 的「指标」名 → 标准字段
_FIN_KEYS = {
    "归母净利润": "net_profit", "营业总收入": "revenue", "净资产收益率(ROE)": "roe",
    "净资产收益率": "roe", "销售毛利率": "gross_margin", "销售净利率": "net_margin",
    "基本每股收益": "eps", "资产负债率": "debt_ratio",
}


@_robust
def financial_abstract(code: str) -> dict:
    """关键财务指标 + 同比增速（最近报告期 vs 去年同期）。"""
    df = ak.stock_financial_abstract(symbol=code)
    if df is None or df.empty:
        return {}
    # 列：选项, 指标, <报告期1>, <报告期2>, ...（报告期降序）
    periods = [c for c in df.columns if c not in ("选项", "指标")]
    if len(periods) < 5:
        return {}
    latest, year_ago = periods[0], periods[4]  # 同比：往前推4个季度
    out = {"report_period": latest}
    idx = df.set_index("指标")
    for ind, field in _FIN_KEYS.items():
        if ind in idx.index:
            cur = pd.to_numeric(idx.loc[ind, latest], errors="coerce")
            if isinstance(cur, pd.Series):
                cur = cur.iloc[0]
            out[field] = round(float(cur), 4) if pd.notna(cur) else None
            # 营收/净利的同比增速
            if field in ("revenue", "net_profit"):
                prev = pd.to_numeric(idx.loc[ind, year_ago], errors="coerce")
                if isinstance(prev, pd.Series):
                    prev = prev.iloc[0]
                if pd.notna(cur) and pd.notna(prev) and prev != 0:
                    out[f"{field}_yoy"] = round((cur / prev - 1) * 100, 2)
    return out


# ---------------------------------------------------------------- 分红

# 分红同走东财，断流可降级，调小重试快速失败（理由同 chip_distribution）。
@_robust(attempts=2, max_wait=1.0)
def dividend(code: str) -> dict:
    """最近一期分红方案与股息率（若有）。"""
    df = ak.stock_fhps_detail_em(symbol=code)
    if df is None or df.empty:
        return {}
    r = df.iloc[-1]
    g = lambda *ks: next((float(r[k]) for k in ks if k in r and pd.notna(r[k])), None)
    return {
        "report_period": str(r.get("报告期", "")),
        "dividend_yield": g("股息率", "股息率-已上市部分"),
        "payout_per_10": g("现金分红-现金分红比例", "现金分红"),
    }


# ---------------------------------------------------------------- 基本面聚合（per-stock）

def context(code: str, valuation_row: dict | None = None) -> dict:
    """聚合单只股票的基本面上下文，各维度独立降级（取数失败不影响其他）。

    valuation_row: 可传入已缓存的估值行（来自 fundamental 表）以省去实时取数；
                   不传则尝试从全市场快照里捞（较重，建议传缓存）。
    """
    ctx = {"valuation": valuation_row or {}, "financial": {}, "chip": {}, "dividend": {}}
    for key, fn in (("financial", lambda: financial_abstract(code)),
                    ("chip", lambda: chip_distribution(code)),
                    ("dividend", lambda: dividend(code))):
        try:
            ctx[key] = fn() or {}
        except Exception:
            ctx[key] = {}
    return ctx
