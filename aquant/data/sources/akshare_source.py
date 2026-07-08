"""AkShare 数据源适配器。

职责：从网络取数 → 规整成标准英文列 DataFrame，不碰存储。

两个关键工程问题已处理：
1. 代理偏好相反：东财不同子接口对本机 Clash 代理偏好相反（日线走代理才通，
   板块/资金流直连才通）。故每次调用在「走代理 / 直连」间交替重试，见 _robust。
2. 大区间断流：eastmoney 日线对跨多年大区间会主动断开，故按自然年分段拉取再拼接。

标准列约定：股票标识统一为 code（6 位字符串），日期为 date（YYYY-MM-DD 字符串）。
"""
from __future__ import annotations

import functools
import os
import socket
import time

import akshare as ak
import pandas as pd
import requests.utils

from ... import config

# 全局 socket 超时兜底：akshare 内部请求不暴露 timeout，东财「大区间断流」时
# socket 读会永久阻塞、单次调用不抛异常，导致 _robust 的重试无法触发、整批任务卡死。
# 设默认超时后，卡住的连接会抛异常 → 被 _robust 接住重试 → 最终走熔断/兜底源。
# requests.get 显式指定的 timeout 不受影响（显式值优先）。
_SOCKET_TIMEOUT = getattr(config, "SOCKET_TIMEOUT", 25.0)
socket.setdefaulttimeout(_SOCKET_TIMEOUT)

# --- 代理交替重试 -----------------------------------------------------------
# 东财不同子接口对本机 Clash 代理偏好相反：
#   日线 push2his.eastmoney —— 走代理才通，直连被重置；
#   板块/资金流 push2.eastmoney —— 直连才通，走代理丢连。
# 任何固定策略都会挂一半，故每次调用在「走代理 / 直连」间交替重试，谁通用谁。
_REAL_PROXIES = {k: v for k, v in {
    "http": os.getenv("HTTP_PROXY") or os.getenv("http_proxy"),
    "https": os.getenv("HTTPS_PROXY") or os.getenv("https_proxy"),
}.items() if v}

_orig_getproxies = requests.utils.getproxies

# 进程启动时捕获的真实代理环境变量（来自 Clash 等），供「走代理」分支恢复。
_PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                   "ALL_PROXY", "all_proxy")
_ORIG_PROXY_ENV = {k: os.environ.get(k) for k in _PROXY_ENV_KEYS}


def _set_proxy(use_proxy: bool) -> None:
    """切换本次请求走代理 / 直连。

    不仅覆盖 requests.utils.getproxies，还同步增删 os.environ 的代理变量——
    akshare 底层部分请求直接读环境变量、绕过 getproxies 覆盖，故直连分支必须
    连环境代理一起清掉，否则板块/资金流（push2，必须直连）会被 Clash 代理
    RemoteDisconnected（曾导致 run-daily 板块每次自动跳过）。
    """
    if use_proxy and _REAL_PROXIES:
        requests.utils.getproxies = lambda: dict(_REAL_PROXIES)
        for k, v in _ORIG_PROXY_ENV.items():
            if v is not None:
                os.environ[k] = v
    else:
        requests.utils.getproxies = lambda: {}
        for k in _PROXY_ENV_KEYS:
            os.environ.pop(k, None)


def _robust(fn=None, *, attempts: int | None = None, max_wait: float = 12.0):
    """交替代理/直连的强重试装饰器。偶数次走代理、奇数次直连，谁通用谁。

    attempts: 重试次数；有兜底源的调用可调小以快速失败（默认 RETRY_ATTEMPTS+4）。
    """
    n = attempts if attempts is not None else config.RETRY_ATTEMPTS + 4

    def deco(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            last = None
            for i in range(n):
                _set_proxy(use_proxy=(i % 2 == 0))
                try:
                    return f(*args, **kwargs)
                except Exception as e:  # noqa: BLE001 akshare 异常类型杂，统一兜底
                    last = e
                    if i < n - 1:
                        time.sleep(min(0.8 * (1.5 ** i), max_wait))
            raise last
        return wrapper

    return deco(fn) if fn is not None else deco


def infer_market(code: str) -> str:
    """根据代码前缀推断交易所，用于需要 market 前缀的接口。"""
    if code.startswith(("60", "68", "9")):
        return "sh"
    if code.startswith(("8", "4")):
        return "bj"
    return "sz"


# ---------------------------------------------------------------- 股票列表

@_robust
def stock_list() -> pd.DataFrame:
    """全 A 股代码与名称。columns=[code, name, market]。"""
    df = ak.stock_info_a_code_name()
    df["code"] = df["code"].astype(str).str.zfill(6)
    df["market"] = df["code"].map(infer_market)
    return df[["code", "name", "market"]].copy()


# ---------------------------------------------------------------- 日线

_BAR_MAP = {
    "日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close",
    "成交量": "volume", "成交额": "amount", "涨跌幅": "pct_chg", "换手率": "turnover",
}


_STD_COLS = ["code", "date", "open", "high", "low", "close",
             "volume", "amount", "pct_chg", "turnover"]

# 东财熔断器：限流/宕机时连续失败 N 次后直接跳过东财、全程走新浪兜底，
# 每隔 _EM_PROBE_EVERY 次调用再放行一次探测，避免长批量任务把时间浪费在死源上。
_EM_FAIL_THRESHOLD = 3
_EM_PROBE_EVERY = 200
_em = {"consec_fail": 0, "open": False, "calls_since_open": 0}


def _em_allowed() -> bool:
    if not _em["open"]:
        return True
    _em["calls_since_open"] += 1
    if _em["calls_since_open"] >= _EM_PROBE_EVERY:  # 周期性探测恢复
        _em["calls_since_open"] = 0
        return True
    return False


def _em_record(ok: bool) -> None:
    if ok:
        _em["consec_fail"] = 0
        _em["open"] = False
        _em["calls_since_open"] = 0
    else:
        _em["consec_fail"] += 1
        if _em["consec_fail"] >= _EM_FAIL_THRESHOLD:
            _em["open"] = True


@_robust(attempts=3, max_wait=3.0)
def _bar_chunk_em(code: str, start: str, end: str, ak_adjust: str) -> pd.DataFrame:
    """东方财富日线（单区间）。有新浪兜底，故少重试、快速失败。"""
    raw = ak.stock_zh_a_hist(symbol=code, period="daily",
                             start_date=start, end_date=end, adjust=ak_adjust)
    return raw if raw is not None else pd.DataFrame()


@_robust
def _daily_sina(code: str, start: str, end: str, ak_adjust: str) -> pd.DataFrame:
    """新浪日线兜底（一次取全区间）。symbol 需带交易所前缀。"""
    sym = infer_market(code) + code
    raw = ak.stock_zh_a_daily(symbol=sym, start_date=start, end_date=end,
                              adjust=ak_adjust or "")
    return raw if raw is not None else pd.DataFrame()


def _standardize(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """把任一源的日线规整到标准列，缺 pct_chg 则由收盘价算。"""
    df = df.rename(columns=_BAR_MAP).copy()
    df["code"] = code
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    if "pct_chg" not in df.columns and "close" in df.columns:
        df["pct_chg"] = (df["close"].pct_change() * 100).round(4)
    return df[[c for c in _STD_COLS if c in df.columns]]


def daily_bar(code: str, start: str | None = None, end: str | None = None,
              adjust: str | None = None) -> pd.DataFrame:
    """单只股票日线（默认前复权），按日期升序。

    多源兜底：先东方财富（跨年按自然年分段，规避断流）；东财不可用（如限流）
    时自动切换新浪。任一源成功即返回标准列：
    code,date,open,high,low,close,volume,amount,pct_chg,turnover
    """
    start = start or config.HISTORY_START
    end = end or pd.Timestamp.today().strftime("%Y%m%d")
    adjust = adjust if adjust is not None else config.ADJUST
    ak_adjust = "" if adjust in ("none", "", None) else adjust

    # 源 1：东方财富（分年）。熔断打开时跳过，避免在死源上空耗。
    if _em_allowed():
        try:
            start_ts, end_ts = pd.to_datetime(start), pd.to_datetime(end)
            parts = []
            for year in range(start_ts.year, end_ts.year + 1):
                seg_s = max(start_ts, pd.Timestamp(year, 1, 1)).strftime("%Y%m%d")
                seg_e = min(end_ts, pd.Timestamp(year, 12, 31)).strftime("%Y%m%d")
                chunk = _bar_chunk_em(code, seg_s, seg_e, ak_adjust)
                if not chunk.empty:
                    parts.append(chunk)
            if parts:
                _em_record(ok=True)
                return _standardize(pd.concat(parts, ignore_index=True), code)
            _em_record(ok=False)  # 空结果也算失败（多为限流）
        except Exception:
            _em_record(ok=False)  # 落到新浪兜底

    # 源 2：新浪
    raw = _daily_sina(code, start, end, ak_adjust)
    if raw is not None and not raw.empty:
        return _standardize(raw, code)
    return pd.DataFrame()


# ---------------------------------------------------------------- 个股资金流（全市场单日快照）

_FLOW_MAP = {
    "代码": "code", "名称": "name", "最新价": "close", "今日涨跌幅": "pct_chg",
    "今日主力净流入-净额": "main_net", "今日主力净流入-净占比": "main_net_pct",
    "今日超大单净流入-净额": "xl_net", "今日大单净流入-净额": "lg_net",
    "今日中单净流入-净额": "md_net", "今日小单净流入-净额": "sm_net",
}


@_robust
def fund_flow_rank(indicator: str = "今日") -> pd.DataFrame:
    """全市场个股资金流排名快照（主力/超大/大/中/小单净流入）。"""
    df = ak.stock_individual_fund_flow_rank(indicator=indicator).rename(columns=_FLOW_MAP)
    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.zfill(6)
    keep = [c for c in _FLOW_MAP.values() if c in df.columns]
    out = df[keep].copy()
    for c in out.columns:
        if c not in ("code", "name"):
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


@_robust
def fund_flow_top(n: int = 100, direction: str = "in") -> pd.DataFrame:
    """主力资金净流入/流出排行榜前 n（直连东财 clist，一次请求，避免 53 页爬取断流）。

    direction='in' 取净流入 Top n（降序），'out' 取净流出 Top n（升序）。
    返回 code,name,close,pct_chg,main_net,main_net_pct。
    """
    import requests
    params = {
        "pn": "1", "pz": str(n), "po": "1" if direction == "in" else "0",
        "np": "1", "fltt": "2", "invt": "2", "fid": "f62",
        "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:7,m:1+t:3",
        "fields": "f12,f14,f2,f3,f62,f184",
    }
    r = requests.get("https://push2.eastmoney.com/api/qt/clist/get",
                     params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    data = r.json()["data"]["diff"]
    df = pd.DataFrame(data).rename(columns={
        "f12": "code", "f14": "name", "f2": "close", "f3": "pct_chg",
        "f62": "main_net", "f184": "main_net_pct"})
    df["code"] = df["code"].astype(str).str.zfill(6)
    for c in ("close", "pct_chg", "main_net", "main_net_pct"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["code", "name", "close", "pct_chg", "main_net", "main_net_pct"]]


# ---------------------------------------------------------------- 行业板块

@_robust
def industry_snapshot() -> pd.DataFrame:
    """行业板块当日快照：sector/sector_code/pct_chg/turnover/up_count/down_count/leader。"""
    rename = {"板块名称": "sector", "板块代码": "sector_code", "涨跌幅": "pct_chg",
              "换手率": "turnover", "上涨家数": "up_count", "下跌家数": "down_count",
              "领涨股票": "leader", "最新价": "price", "总市值": "mkt_cap"}
    df = ak.stock_board_industry_name_em().rename(columns=rename)
    keep = [c for c in rename.values() if c in df.columns]
    return df[keep].copy()


@_robust
def industry_members(sector: str) -> pd.DataFrame:
    """某行业板块成分股。columns=[sector, code, name]。"""
    df = ak.stock_board_industry_cons_em(symbol=sector).rename(columns={"代码": "code", "名称": "name"})
    df["code"] = df["code"].astype(str).str.zfill(6)
    df["sector"] = sector
    return df[["sector", "code", "name"]].copy()


_SECTOR_FLOW_MAP = {
    "名称": "sector", "今日涨跌幅": "pct_chg", "今日主力净流入-净额": "main_net",
    "今日主力净流入-净占比": "main_net_pct", "今日主力净流入最大股": "leader",
}


@_robust
def sector_fund_flow() -> pd.DataFrame:
    """行业板块资金流：各板块今日主力净额/净占比/领涨股。columns=[sector,pct_chg,main_net,main_net_pct,leader]。"""
    df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流").rename(columns=_SECTOR_FLOW_MAP)
    keep = [c for c in _SECTOR_FLOW_MAP.values() if c in df.columns]
    out = df[keep].copy()
    for c in ("pct_chg", "main_net", "main_net_pct"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


# ---------------------------------------------------------------- 指数日线

@_robust
def index_daily(index_code: str = "sh000300") -> pd.DataFrame:
    """宽基指数日线（新浪源）。index_code 如 sh000300(沪深300)/sh000905(中证500)。

    返回 columns=[code, date, close]（够 regime/基准用；如需 OHLC 可扩展）。
    """
    df = ak.stock_zh_index_daily(symbol=index_code)
    df = df.rename(columns={"date": "date", "close": "close"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["code"] = index_code
    return df[["code", "date", "close"]].sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------- 现价快照

_SPOT_MAP = {"代码": "code", "名称": "name", "最新价": "close",
             "涨跌幅": "pct_chg", "换手率": "turnover", "成交额": "amount"}


@_robust
def spot_snapshot() -> pd.DataFrame:
    """全市场现价快照（盘中分钟级）。columns=[code,name,close,pct_chg,turnover,amount]。"""
    df = ak.stock_zh_a_spot_em().rename(columns=_SPOT_MAP)
    df["code"] = df["code"].astype(str).str.zfill(6)
    keep = list(_SPOT_MAP.values())
    return df[[c for c in keep if c in df.columns]].copy()


# ---------------------------------------------------------------- 龙虎榜

@_robust
def lhb_detail(start: str, end: str) -> pd.DataFrame:
    """龙虎榜明细（日期区间，YYYYMMDD）。"""
    rename = {"代码": "code", "名称": "name", "上榜日": "date", "解读": "reason",
              "收盘价": "close", "涨跌幅": "pct_chg", "龙虎榜净买额": "lhb_net_buy",
              "龙虎榜成交额": "lhb_amount"}
    df = ak.stock_lhb_detail_em(start_date=start, end_date=end).rename(columns=rename)
    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.zfill(6)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    keep = [c for c in dict.fromkeys(rename.values()) if c in df.columns]
    return df[keep].copy()


@_robust
def lhb_seats(code: str, date: str, flag: str) -> pd.DataFrame:
    """个股龙虎榜席位明细。flag='买入'/'卖出'，date=YYYY-MM-DD 或 YYYYMMDD。"""
    d = str(date).replace("-", "")
    rename = {"序号": "rank", "交易营业部名称": "seat", "买入金额": "buy",
              "卖出金额": "sell", "净额": "net"}
    df = ak.stock_lhb_stock_detail_em(
        symbol=str(code).zfill(6), date=d, flag=flag).rename(columns=rename)
    keep = [c for c in ("rank", "seat", "buy", "sell", "net") if c in df.columns]
    out = df[keep].copy()
    for col in ("buy", "sell", "net"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


# ---------------------------------------------------------------- 涨停梯队 / 北向

@_robust
def limit_pool(date: str) -> pd.DataFrame:
    """涨停池（date=YYYY-MM-DD 或 YYYYMMDD）：连板数/封板资金/炸板次数/行业。"""
    d = str(date).replace("-", "")
    rename = {"代码": "code", "名称": "name", "涨跌幅": "pct_chg", "成交额": "amount",
              "换手率": "turnover", "封板资金": "seal_fund", "炸板次数": "break_times",
              "连板数": "boards", "所属行业": "industry", "首次封板时间": "first_seal_time"}
    df = ak.stock_zt_pool_em(date=d).rename(columns=rename)
    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.zfill(6)
    keep = [c for c in dict.fromkeys(rename.values()) if c in df.columns]
    out = df[keep].copy()
    for col in ("pct_chg", "amount", "turnover", "seal_fund", "break_times", "boards"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


@_robust
def north_summary() -> pd.DataFrame:
    """北向资金汇总：market(沪股通/深股通/港股通…) + net(资金净流入)。"""
    df = ak.stock_hsgt_fund_flow_summary_em().rename(
        columns={"板块": "market", "资金净流入": "net"})
    keep = [c for c in ("market", "net") if c in df.columns]
    out = df[keep].copy()
    if "net" in out.columns:
        out["net"] = pd.to_numeric(out["net"], errors="coerce")
    return out
