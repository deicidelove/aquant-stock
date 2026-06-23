"""Streamlit 看盘工作台（深色 Bloomberg 风）。

运行：streamlit run aquant/dashboard/app.py
9 页：概览/大盘/决策/模拟盘/网格/个股/选股/资金流/板块。
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aquant.data import store
from aquant.dashboard import theme
from aquant.dashboard.kline import kline_figure
from aquant.select import scorer
from aquant.signal import timing

st.set_page_config(page_title="aquant 量化投研驾驶舱", layout="wide", page_icon="📈")


@st.cache_data(ttl=300)
def _summary():
    return store.summary()


@st.cache_data(ttl=600, show_spinner="全市场打分中（首次约30-60秒，之后缓存秒开）…")
def _scored(top: int, use_ic: bool):
    from aquant import research
    w = scorer.IC_WEIGHTS if use_ic else scorer.MOMENTUM_WEIGHTS
    return scorer.score_fast(codes=research.universe(), weights=w, top=top)


@st.cache_data(ttl=600, show_spinner="多维融合分析中…")
def _stock_decision(code: str):
    """按 code 缓存的个股决策（含基本面/资讯实时取数），避免每次切票重复联网。"""
    from aquant import research
    rep = research.stock_report(code, market_scores=_scored(10000, True))
    return research.decision(code, rep=rep)


@st.cache_data(ttl=600)
def _regime():
    try:
        from aquant import market
        return market.regime() or {}
    except Exception:
        return {}


# ---------------------------------------------------------------- 主题化表格

_SIG_CLS = {"买入/增持": "b-buy", "持有/观望": "b-hold", "回避/减持": "b-avoid",
            "买入": "b-buy", "持有": "b-hold", "卖出": "b-avoid", "空仓": "b-avoid"}
_RISK_CLS = {"低": "r-low", "中": "r-mid", "高": "r-high"}


def _num(v, pos_color=True):
    try:
        f = float(v)
        cls = ("aq-up" if f > 0 else "aq-down" if f < 0 else "") if pos_color else ""
        return f'<span class="{cls}">{v}</span>'
    except Exception:
        return str(v)


@st.cache_data(ttl=600)
def _mini_kline_svg(code: str, n: int = 40) -> str:
    """近 n 日蜡烛图的轻量内联 SVG（用于名称悬浮预览，无外部依赖）。"""
    try:
        df = store.query(
            "SELECT date, open, high, low, close FROM daily_bar WHERE code=? "
            "ORDER BY date DESC LIMIT ?", [str(code), n])
    except Exception:
        return ""
    if df is None or df.empty or len(df) < 3:
        return ""
    df = df.iloc[::-1].reset_index(drop=True)  # 时间正序
    W, H, padx, ptop, pbot = 240, 110, 6, 18, 8
    lo, hi = float(df["low"].min()), float(df["high"].max())
    rng = (hi - lo) or 1.0
    m = len(df)
    cw = (W - 2 * padx) / m

    def y(v):
        return ptop + (hi - v) / rng * (H - ptop - pbot)

    parts = []
    for i, rr in df.iterrows():
        o, h, l, c = float(rr.open), float(rr.high), float(rr.low), float(rr.close)
        col = "#ff3b47" if c >= o else "#19c39a"  # 红涨绿跌
        cx = padx + i * cw + cw / 2
        parts.append(f'<line x1="{cx:.1f}" y1="{y(h):.1f}" x2="{cx:.1f}" y2="{y(l):.1f}" stroke="{col}" stroke-width="1"/>')
        bw = max(cw * 0.6, 1.2)
        top, bh = min(y(o), y(c)), max(abs(y(c) - y(o)), 1)
        parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}"/>')
    first, last = float(df["close"].iloc[0]), float(df["close"].iloc[-1])
    chg = (last / first - 1) * 100 if first else 0.0
    lab = (f'<text x="{padx}" y="12" fill="#8595ad" font-size="9" font-family="monospace">'
           f'{df["date"].iloc[0][2:]}~{df["date"].iloc[-1][5:]} {m}日 {chg:+.1f}%</text>')
    return (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
            f'style="background:#0a0f18;border-radius:4px;display:block">{lab}{"".join(parts)}</svg>')


def decision_table(df: pd.DataFrame):
    """荐股/决策 主题化表格（信号、风险徽章）。名称悬浮显示近期 K 线。"""
    cols = list(df.columns)
    head = "".join(f"<th>{c}</th>" for c in cols)
    rows = []
    for r in df.itertuples(index=False):
        d = dict(zip(cols, r))
        code_val = d.get("code") or d.get("代码") or ""
        cells = []
        for c in cols:
            v = d[c]
            if c == "code" or c == "代码":
                cells.append(f'<td class="aq-code">{v}</td>')
            elif c == "name" or c == "名称":
                svg = _mini_kline_svg(str(code_val)) if code_val else ""
                if svg:
                    cells.append(f'<td class="aq-name"><span class="aq-knm">{v}'
                                 f'<span class="aq-kpop">{svg}</span></span></td>')
                else:
                    cells.append(f'<td class="aq-name">{v}</td>')
            elif c in ("信号", "signal"):
                cells.append(f'<td><span class="aq-badge {_SIG_CLS.get(str(v),"b-hold")}">{v}</span></td>')
            elif c in ("风险",):
                cells.append(f'<td class="{_RISK_CLS.get(str(v),"")}">{v}</td>')
            elif c in ("综合分", "score", "综合"):
                cells.append(f'<td style="font-weight:800;font-size:.92rem">{v}</td>')
            elif c in ("买点", "目标"):
                cells.append(f'<td class="aq-up">{v}</td>')
            elif c in ("止损",):
                cells.append(f'<td class="aq-down">{v}</td>')
            elif c in ("利好",):
                full = str(v or "")
                cells.append(f'<td class="aq-up aq-news" title="{full}">{full or "—"}</td>')
            elif c in ("利空",):
                full = str(v or "")
                cells.append(f'<td class="aq-down aq-news" title="{full}">{full or "—"}</td>')
            else:
                cells.append(f"<td>{v}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(f'<table class="aq-table"><thead><tr>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)


# ---------------------------------------------------------------- 驾驶舱

@st.cache_data(ttl=1800, show_spinner="驾驶舱首次加载（多维研判，约20-40秒，之后缓存）…")
def _cockpit_brief(n: int):
    from aquant import research
    return research.briefing(top=n)


def _decision_card(d: dict):
    """紧凑个股决策卡（HTML）。"""
    if not d:
        st.info("无焦点标的")
        return
    p = d["battle_plan"]
    sig_cls = _SIG_CLS.get(d["signal"], "b-hold")
    rk = _RISK_CLS.get(d.get("risk_level", ""), "")
    parts = d["score_parts"]
    seg = "".join(
        f'<span style="display:inline-block;height:7px;width:{max(v,0)/100*100:.0f}%;'
        f'background:{c}"></span>'
        for v, c in zip(parts.values(), ["#3fa7ff", theme.AMBER, theme.UP, theme.DOWN]))
    st.markdown(f"""
    <div class="aq-panel" style="margin:0">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <div style="font-size:1.8rem;font-weight:800;color:#fff;font-variant-numeric:tabular-nums">{d['total_score']}</div>
        <div>
          <div class="aq-name" style="font-size:1.05rem">{d['name']} <span class="aq-code">{d['code']}</span></div>
          <span class="aq-badge {sig_cls}">{d['signal']}</span>
          <span style="margin-left:8px;font-family:PingFang SC;font-size:.7rem" class="{rk}">风险 {d.get('risk_level','-')}</span>
        </div>
      </div>
      <div style="display:flex;height:7px;border-radius:3px;overflow:hidden;background:#0a0f18;margin-bottom:12px">{seg}</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#1d2940;border-radius:4px;overflow:hidden;font-variant-numeric:tabular-nums">
        <div style="background:#131c2b;padding:7px;text-align:center"><div style="font-size:.58rem;color:#566077;font-family:PingFang SC">现价</div><div style="font-weight:700">{d['close']}</div></div>
        <div style="background:#131c2b;padding:7px;text-align:center"><div style="font-size:.58rem;color:#566077;font-family:PingFang SC">买点</div><div style="font-weight:700" class="aq-up">{p['ideal_buy']}</div></div>
        <div style="background:#131c2b;padding:7px;text-align:center"><div style="font-size:.58rem;color:#566077;font-family:PingFang SC">止损</div><div style="font-weight:700" class="aq-down">{p['stop_loss']}</div></div>
        <div style="background:#131c2b;padding:7px;text-align:center"><div style="font-size:.58rem;color:#566077;font-family:PingFang SC">目标</div><div style="font-weight:700" class="aq-up">{p['take_profit']}</div></div>
      </div>
    </div>""", unsafe_allow_html=True)


def page_cockpit():
    from aquant import market, sector
    from aquant.paper import account, simulate
    c = st.columns([1.05, 1.25, 1])

    # —— 大盘复盘 ——
    with c[0]:
        theme.panel_header("大盘复盘", "REGIME")
        r = _regime()
        if r:
            b = r["breadth"]
            st.markdown(f"""
            <div class="aq-panel" style="margin:0">
              <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:8px">
                <span style="font-family:PingFang SC;font-size:1.5rem;font-weight:800;color:{theme.AMBER}">{r['state']}</span>
                <span style="font-size:.7rem;color:#8595ad;font-family:PingFang SC">{r['score']}/7 · 建议 {r['suggested_position']}</span>
              </div>
              <div style="font-family:PingFang SC;font-size:.72rem;color:#8595ad;margin-bottom:10px">{r['note']}</div>
              {_bar('站上MA20', b['above_ma20_pct'])}{_bar('站上MA60', b['above_ma60_pct'])}{_bar('上涨家数占比', b['up_ratio'])}
            </div>""", unsafe_allow_html=True)

    # —— 模拟盘 ——
    with c[1]:
        theme.panel_header("模拟盘", "PAPER")
        if store.has_table("paper_nav"):
            nav = account.nav_series(); ld = nav["date"].iloc[-1]
            init = account._meta("init_capital", account.INIT_CAPITAL)
            total = account.total_value(ld); perf = simulate.performance()
            theme.kpi_row([
                {"label": "总资产", "value": f"{total/1e4:.1f}", "sub": "万", "color": "up" if total >= init else "down"},
                {"label": "累计", "value": f"{perf.get('total_return',0)*100:+.1f}%", "color": "auto"},
                {"label": "超额", "value": f"{perf.get('excess',0)*100:+.1f}%", "color": "auto"},
            ])
            eq = nav.set_index("date")["total"] / nav["total"].iloc[0]
            bench = simulate._benchmark(eq.index)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=list(eq.index), y=eq.values, name="模拟盘", line=dict(color=theme.UP, width=2)))
            if bench is not None:
                fig.add_trace(go.Scatter(x=list(bench.index), y=bench.values, name="沪深300", line=dict(color=theme.INK2, width=1.4, dash="dash")))
            fig.update_layout(height=180, legend=dict(orientation="h", y=1.2, x=0, font=dict(size=9)))
            st.plotly_chart(theme.style_fig(fig), width="stretch", config={"displayModeBar": False})
        else:
            st.info("`paper-seed` 建仓后显示")

    # —— 焦点个股（#1 荐股的多维决策）——
    with c[2]:
        theme.panel_header("焦点个股", "FOCUS")
        try:
            from aquant import research
            top1 = _scored(1, True)
            if not top1.empty:
                _decision_card(research.decision(top1["code"].iloc[0]))
        except Exception:
            st.info("数据不足")

    # —— 板块主线 ——
    theme.panel_header("板块主线 · 资金共识", "SECTOR LEADERS")
    ml = sector.main_lines(6)
    if not ml.empty:
        mx = ml["pct_chg"].max() or 1
        bars = "".join(
            f'<div class="sec" style="display:flex;align-items:center;gap:10px;margin-bottom:7px">'
            f'<span style="font-family:PingFang SC;font-size:.76rem;width:130px;flex:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{r.sector}</span>'
            f'<span style="flex:1;height:8px;background:#0a0f18;border:1px solid #1d2940;border-radius:2px;overflow:hidden">'
            f'<i style="display:block;height:100%;width:{r.pct_chg/mx*100:.0f}%;background:linear-gradient(90deg,#7a1f27,{theme.UP})"></i></span>'
            f'<span class="aq-up" style="width:60px;text-align:right;font-weight:700">{r.pct_chg:+.2f}%</span></div>'
            for r in ml.itertuples(index=False))
        st.markdown(f'<div class="aq-panel">{bars}</div>', unsafe_allow_html=True)

    # —— 荐股决策表 ——
    theme.panel_header("荐股研报快览 · 多维决策", "DECISION SCREEN")
    decision_table(_cockpit_brief(8))


def _bar(label, pct):
    return (f'<div style="margin:6px 0"><div style="display:flex;justify-content:space-between;'
            f'font-size:.66rem;color:#8595ad;margin-bottom:3px"><span style="font-family:PingFang SC">{label}</span>'
            f'<span class="aq-down">{pct}%</span></div>'
            f'<div style="height:6px;background:#0a0f18;border:1px solid #1d2940;border-radius:3px;overflow:hidden">'
            f'<div style="height:100%;width:{min(pct,100)}%;background:linear-gradient(90deg,#103f37,{theme.DOWN})"></div></div></div>')


# ---------------------------------------------------------------- 页面

def page_overview():
    theme.panel_header("本地仓库概览", "DATA WAREHOUSE")
    s = _summary()
    if s.empty:
        st.info("仓库为空。先 `python -m aquant.cli update-all` 入库。")
        return
    theme.kpi_row([
        {"label": "覆盖股票", "value": f"{len(s)}", "sub": " 只"},
        {"label": "日线总行数", "value": f"{int(s['rows'].sum())/1e4:.0f}", "sub": " 万"},
        {"label": "最新交易日", "value": str(s["end"].max())},
        {"label": "最早数据", "value": str(s["start"].min())},
    ])
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.dataframe(s, width="stretch", height=420)


def page_market():
    theme.panel_header("大盘复盘 + 中观主线（自上而下）", "TOP-DOWN")
    from aquant import market, sector
    c = st.columns([1, 1])
    with c[0]:
        st.markdown('<div class="aq-panel">', unsafe_allow_html=True)
        st.markdown(market.review_markdown())
        st.markdown('</div>', unsafe_allow_html=True)
    with c[1]:
        st.markdown('<div class="aq-panel">', unsafe_allow_html=True)
        st.markdown(sector.review_markdown())
        st.markdown('</div>', unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)
def _picks_cached(top, sig, uptrend, drop_boards, min_amount):
    """缓存选股结果，键含板块/流动性过滤——同参数秒开，切换才重算。"""
    from aquant import research
    return research.daily_picks(
        top=top, signal=sig, require_uptrend=uptrend,
        drop_boards=set(drop_boards) if drop_boards else None, min_amount=min_amount)


def page_decision():
    theme.panel_header("每日选股决策（选股 + 择时 + 关键价位）", "DECISION")
    from aquant import research
    s = _summary()
    if s.empty or len(s) < 3:
        st.info("仓库数据不足，先入库。")
        return
    c = st.columns([1, 1, 1])
    top = c[0].slider("候选数", 5, 50, 20)
    sig = c[1].selectbox("择时信号", list(timing.SIGNALS))
    uptrend = c[2].checkbox("叠加上涨过滤（价>MA60）", value=False)
    f = st.columns([2, 1])
    drop = f[0].multiselect("剔除板块（缩小股票域并提速；ST/退/次新已默认剔除）",
                            ["科创", "创业", "北交"], default=[])
    min_amt = f[1].select_slider("最低日均成交额", options=[3e7, 5e7, 1e8, 2e8, 5e8],
                                 value=5e7, format_func=lambda v: f"{v/1e8:.2f}亿")
    with st.spinner("打分 + 择时计算中…（同参数已缓存，切换板块仅首次重算）"):
        picks = _picks_cached(top, sig, uptrend, tuple(drop), float(min_amt))
    if picks.empty:
        st.warning("无符合条件标的。")
        return
    st.caption("将鼠标悬停在股票名称上可预览近 40 日 K 线")
    disp = picks.rename(columns={
        "score": "综合分", "action": "动作", "close": "现价", "ma20": "MA20",
        "ma60": "MA60", "support": "支撑", "resistance": "压力", "stop": "止损",
        "signal_date": "信号日"})
    decision_table(disp)
    buys = picks[picks["action"] == "买入"]
    if not buys.empty:
        st.success(f"今日出现「买入」信号：{', '.join(buys['name'].fillna(buys['code']))}")

    st.divider()
    theme.panel_header("荐股研报快览 · 多维决策", "DECISION SCREEN")
    nb = st.slider("快览数量", 5, 20, 10, key="brief_n")
    if st.button("生成研报快览（逐只抓基本面+资讯，稍慢）"):
        @st.cache_data(ttl=1800)
        def _brief(n):
            return research.briefing(top=n)
        with st.spinner("多维研判中…"):
            bf = _brief(nb)
        decision_table(bf)


def page_paper():
    theme.panel_header("模拟盘 · 闭环回放（推荐→建仓→盯市→归因）", "PAPER")
    from aquant.paper import account, simulate
    if not store.has_table("paper_nav"):
        st.info("模拟盘为空。`python -m aquant.cli paper-seed` 回放建仓。")
        return
    nav = account.nav_series()
    last_date = nav["date"].iloc[-1]
    init_cap = account._meta("init_capital", account.INIT_CAPITAL)
    cash = account.cash()
    total = account.total_value(last_date)
    pos = account.positions()
    pnl = total - init_cap
    st.caption(f"起始 {nav['date'].iloc[0]}　→　截至 {last_date}")
    theme.kpi_row([
        {"label": "初始资金", "value": f"{init_cap/1e4:.0f}", "sub": "万"},
        {"label": "当前总资产", "value": f"{total/1e4:.1f}", "sub": "万", "color": "up" if pnl >= 0 else "down"},
        {"label": "浮动盈亏", "value": f"{pnl/1e4:+.1f}", "sub": "万", "color": "auto"},
        {"label": "现金", "value": f"{cash/1e4:.1f}", "sub": "万"},
        {"label": "持仓", "value": f"{0 if pos.empty else len(pos)}", "sub": "只"},
    ])
    perf = simulate.performance()
    if perf:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        theme.kpi_row([
            {"label": "累计收益", "value": f"{perf['total_return']*100:+.1f}%", "color": "auto"},
            {"label": "年化", "value": f"{perf.get('annual_return',0)*100:+.1f}%", "color": "auto"},
            {"label": "夏普", "value": f"{perf.get('sharpe',0)}"},
            {"label": "最大回撤", "value": f"{perf['max_drawdown']*100:.1f}%", "color": "down"},
            {"label": "超额(vs沪深300)", "value": f"{perf.get('excess',0)*100:+.1f}%", "color": "auto"},
        ])

    # 净值曲线（plotly 深色，红涨绿跌：模拟盘红、基准灰）
    eq = nav.set_index("date")["total"] / nav["total"].iloc[0]
    bench = simulate._benchmark(eq.index)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(eq.index), y=eq.values, name="模拟盘",
                             line=dict(color=theme.UP, width=2.4)))
    if bench is not None:
        fig.add_trace(go.Scatter(x=list(bench.index), y=bench.values, name="沪深300",
                                 line=dict(color=theme.INK2, width=1.6, dash="dash")))
    fig.update_layout(height=300, legend=dict(orientation="h", y=1.1, x=0))
    st.plotly_chart(theme.style_fig(fig), width="stretch")

    col = st.columns(2)
    attr = simulate.attribution()
    if not attr.empty:
        with col[0]:
            theme.panel_header("盈利 Top10", "WINNERS")
            decision_table(attr.head(10)[["code", "name", "ret", "pnl"]]
                           .rename(columns={"ret": "收益率", "pnl": "盈亏"}))
        with col[1]:
            theme.panel_header("亏损 Top10", "LOSERS")
            decision_table(attr.tail(10).iloc[::-1][["code", "name", "ret", "pnl"]]
                           .rename(columns={"ret": "收益率", "pnl": "盈亏"}))
    with st.expander("交易流水"):
        st.dataframe(store.query("SELECT * FROM paper_trade ORDER BY tid DESC LIMIT 200"), width="stretch")


@st.cache_data(ttl=600)
def _grid_codes(top: int):
    res = _scored(top, True)
    return list(zip(res["code"], res.get("name", res["code"]))) if not res.empty else []


def page_grid():
    theme.panel_header("K线网格速览（荐股区 / 浏览区）", "GRID")
    from aquant.dashboard.kline import mini_figure

    def _grid(items, cols=4):
        for i in range(0, len(items), cols):
            row = st.columns(cols)
            for col, (code, name) in zip(row, items[i:i + cols]):
                with col:
                    st.plotly_chart(theme.style_fig(mini_figure(code, str(name))), width="stretch",
                                    key=f"mini_{code}", config={"displayModeBar": False})

    st.markdown("##### 🎯 荐股（当前 IC 策略 Top）")
    n = st.slider("荐股数量", 4, 24, 12, 4)
    rec = _grid_codes(n)
    rec_codes = {c for c, _ in rec}
    if rec:
        _grid(rec)
    st.divider()
    st.markdown("##### 📋 浏览其他股票")
    mode = st.radio("来源", ["主力资金流入Top", "自选代码"], horizontal=True)
    others = []
    if mode == "主力资金流入Top" and store.has_table("fund_flow"):
        latest = store.query("SELECT max(date) d FROM fund_flow")["d"].iloc[0]
        ff = store.query("SELECT code,name FROM fund_flow WHERE date=? ORDER BY main_net DESC LIMIT 40", [latest])
        others = [(c, n) for c, n in zip(ff["code"], ff["name"]) if c not in rec_codes][:12]
    else:
        s = _summary()
        codes = st.multiselect("选代码", s["code"].tolist() if not s.empty else [], max_selections=12)
        nm = dict(zip(store.query("SELECT code,name FROM stock_basic")["code"],
                      store.query("SELECT code,name FROM stock_basic")["name"])) if store.has_table("stock_basic") else {}
        others = [(c, nm.get(c, "")) for c in codes]
    if others:
        _grid(others)


def page_stock():
    theme.panel_header("个股 · K线 + 决策仪表盘", "FOCUS")
    s = _summary()
    codes = s["code"].tolist() if not s.empty else []
    if not codes:
        st.info("仓库为空，先拉数据。")
        return
    nm = store.query("SELECT code, name FROM stock_basic") if store.has_table("stock_basic") else pd.DataFrame()
    name_map = dict(zip(nm["code"], nm["name"])) if not nm.empty else {}
    col = st.columns([2, 1, 1])
    code = col[0].selectbox("股票（代码 / 名称）", codes,
                            format_func=lambda x: f"{x}　{name_map.get(x, '')}".rstrip())
    last_n = col[1].slider("K线根数", 60, 500, 250, 10)
    sig_name = col[2].selectbox("择时信号", list(timing.SIGNALS))
    st.plotly_chart(theme.style_fig(kline_figure(code, last_n=last_n)), width="stretch")
    with st.expander("📊 决策仪表盘（核心结论 / 作战计划 / 风险 / 基本面 / 资讯 / 因子）", expanded=True):
        from aquant import research
        d = _stock_decision(code)
        st.markdown(research.dashboard_markdown(d))


def page_select():
    theme.panel_header("多因子打分选股（清洁域）", "FACTOR SCREEN")
    s = _summary()
    if s.empty or len(s) < 3:
        st.info("仓库数据不足，先入库。")
        return
    c = st.columns([1, 1])
    top = c[0].slider("候选池 Top-N", 5, 100, 30)
    use_ic = c[1].radio("权重", ["IC加权(验证策略)", "动量风格"], horizontal=True) == "IC加权(验证策略)"
    res = _scored(top, use_ic)
    if res.empty:
        st.warning("无足够历史计算因子。")
        return
    show = [c for c in ["code", "name", "score"] if c in res.columns]
    st.dataframe(res[show], width="stretch")
    fig = px.bar(res, x="code", y="score", color="score",
                 color_continuous_scale=["#1b2433", theme.AMBER])
    st.plotly_chart(theme.style_fig(fig), width="stretch")


def page_fund_flow():
    theme.panel_header("主力资金流向（当日快照）", "CAPITAL FLOW")
    if not store.has_table("fund_flow"):
        st.info("无资金流数据。`python -m aquant.cli flow` 拉取。")
        return
    latest = store.query("SELECT max(date) d FROM fund_flow")["d"].iloc[0]
    df = store.query("SELECT * FROM fund_flow WHERE date = ? ORDER BY main_net DESC", [latest])
    inflow = df[df["main_net"] > 0]
    outflow = df[df["main_net"] < 0].sort_values("main_net")  # 最负在前 = 流出最多
    in_sum = inflow["main_net"].sum() / 1e8
    out_sum = outflow["main_net"].sum() / 1e8
    st.caption(f"日期 {latest}　净流入 {len(inflow)} 只（合计 {in_sum:+.1f} 亿）／"
               f"净流出 {len(outflow)} 只（合计 {out_sum:+.1f} 亿）")

    def _tree(data, title):
        if data.empty:
            st.info("无数据")
            return
        tm = data.copy()
        tm["abs_net"] = tm["main_net"].abs()
        tm["label"] = tm["name"] + " " + (tm["main_net"] / 1e8).round(2).astype(str) + "亿"
        fig = px.treemap(tm, path=["label"], values="abs_net", color="pct_chg",
                         color_continuous_scale=theme.RG_SCALE, color_continuous_midpoint=0,
                         title=title)
        fig.update_layout(height=430)
        st.plotly_chart(theme.style_fig(fig), width="stretch")

    c = st.columns(2)
    with c[0]:
        _tree(inflow.head(30), "主力净流入 Top30（面积=净额，色=涨跌幅）")
    with c[1]:
        _tree(outflow.head(30), "主力净流出 Top30（面积=净额，色=涨跌幅）")

    cc = st.columns(2)
    with cc[0]:
        st.markdown("##### 🔴 净流入 Top20")
        st.dataframe(inflow.head(20), width="stretch")
    with cc[1]:
        st.markdown("##### 🟢 净流出 Top20")
        st.dataframe(outflow.head(20), width="stretch")


def page_sectors():
    theme.panel_header("行业板块轮动", "SECTOR")
    if not store.has_table("sector_daily"):
        st.info("无板块数据。`python -m aquant.cli sectors` 拉取。")
        return
    latest = store.query("SELECT max(date) d FROM sector_daily")["d"].iloc[0]
    df = store.query("SELECT * FROM sector_daily WHERE date = ? ORDER BY pct_chg DESC", [latest])
    st.caption(f"日期 {latest}，共 {len(df)} 个板块")
    if "mkt_cap" in df.columns and df["mkt_cap"].notna().any():
        tm = df.nlargest(60, "mkt_cap")
        fig = px.treemap(tm, path=["sector"], values="mkt_cap", color="pct_chg",
                         color_continuous_scale=theme.RG_SCALE, color_continuous_midpoint=0,
                         title="板块热力图 市值Top60（面积=市值，色=涨跌幅）")
    else:
        fig = px.bar(df.head(20), x="pct_chg", y="sector", orientation="h", color="pct_chg",
                     color_continuous_scale=theme.RG_SCALE, title="板块涨幅")
        fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_layout(height=520)
    st.plotly_chart(theme.style_fig(fig), width="stretch")
    st.dataframe(df, width="stretch")


@st.cache_data(ttl=600, show_spinner="计算推荐前向收益…")
def _track_fr():
    from aquant import track
    return track.forward_returns()


def page_track():
    theme.panel_header("推荐跟踪 · 推荐股事后收益（live 记分卡）", "TRACK")
    if not store.has_table("picks_log"):
        st.info("台账为空。`python -m aquant.cli track-backfill` 历史回放冷启动，"
                "之后每日 `run-daily` 自动留痕。")
        return
    fr = _track_fr()
    if fr.empty:
        st.info("台账为空。先跑 `python -m aquant.cli track-backfill`。")
        return

    HZ = (5, 20, 60)
    live = int((fr["signal"] != "reconstruct").sum())
    st.caption(f"样本 {len(fr)} 条 · {fr['as_of'].nunique()} 个快照日 · "
               f"{fr['as_of'].min()} ~ {fr['as_of'].max()} · "
               f"实时 {live} / 回放 {len(fr)-live}")

    # KPI：各持有期平均超额（红涨绿跌）+ 胜率
    kpis = []
    for hh in HZ:
        exc = fr[f"exc_{hh}"].dropna()
        if exc.empty:
            kpis.append({"label": f"T+{hh} 平均超额", "value": "—", "sub": "pending"})
        else:
            kpis.append({"label": f"T+{hh} 平均超额", "value": f"{exc.mean()*100:+.2f}%",
                         "color": "auto", "sub": f"胜率{(exc > 0).mean()*100:.0f}%"})
    theme.kpi_row(kpis)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    h = st.radio("持有期", HZ, index=2, format_func=lambda x: f"T+{x}", horizontal=True)
    fwd_c, exc_c = f"fwd_{h}", f"exc_{h}"

    c1, c2 = st.columns([3, 2])
    with c1:
        theme.panel_header(f"推荐质量趋势 · 每快照日 Top-N 平均（T+{h}）", "TREND")
        g = fr.groupby("as_of").agg(fwd=(fwd_c, "mean"), exc=(exc_c, "mean")).dropna(how="all")
        if g.empty:
            st.caption("该持有期暂无已结算样本（窗口未到期）。")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=list(g.index), y=(g["fwd"] * 100).values,
                                     name="平均收益%", line=dict(color=theme.AMBER, width=2)))
            fig.add_trace(go.Scatter(x=list(g.index), y=(g["exc"] * 100).values,
                                     name="平均超额%", line=dict(color="#3fa7ff", width=2)))
            fig.add_hline(y=0, line=dict(color=theme.INK2, width=1, dash="dot"))
            fig.update_layout(height=300, legend=dict(orientation="h", y=1.14, x=0))
            st.plotly_chart(theme.style_fig(fig), width="stretch")
    with c2:
        theme.panel_header(f"收益分布 · T+{h} 已结算", "DIST")
        vals = (fr[fwd_c].dropna() * 100)
        if vals.empty:
            st.caption("暂无已结算样本。")
        else:
            fig = go.Figure(go.Histogram(x=vals.values, nbinsx=40, marker_color=theme.AMBER))
            fig.add_vline(x=0, line=dict(color=theme.INK2, width=1, dash="dot"))
            fig.add_vline(x=float(vals.mean()), line=dict(color=theme.UP, width=1.6),
                          annotation_text=f"均值{vals.mean():+.1f}%")
            fig.update_layout(height=300, showlegend=False,
                              xaxis_title="前向收益%", yaxis_title="")
            st.plotly_chart(theme.style_fig(fig), width="stretch")

    theme.panel_header("每只推荐股的前向收益 · 点列头可排序", "DETAIL")
    days = sorted(fr["as_of"].unique(), reverse=True)
    settled = sorted(fr.loc[fr[fwd_c].notna(), "as_of"].unique(), reverse=True)
    default_day = settled[0] if settled else days[0]
    day = st.selectbox("快照日", days, index=days.index(default_day))
    sub = fr[fr["as_of"] == day].copy().sort_values("rank")
    cols = ["rank", "code", "name", "score", "entry_close", "fwd_5", "fwd_20", "fwd_60", exc_c]
    show = sub[[c for c in cols if c in sub.columns]].rename(columns={
        "rank": "排名", "code": "代码", "name": "名称", "score": "综合分",
        "entry_close": "推荐价", "fwd_5": "T+5", "fwd_20": "T+20", "fwd_60": "T+60",
        exc_c: f"超额T+{h}"})
    ret_cols = [c for c in ["T+5", "T+20", "T+60", f"超额T+{h}"] if c in show.columns]

    def _color_col(s):
        out = []
        for v in s:
            if pd.isna(v):
                out.append("color:#566077")
            else:
                out.append(f"color:{theme.UP}" if v > 0 else f"color:{theme.DOWN}" if v < 0 else "")
        return out

    sty = (show.style
           .apply(_color_col, subset=ret_cols)
           .format({c: "{:+.1%}" for c in ret_cols}, na_rep="—")
           .format({"综合分": "{:.2f}", "推荐价": "{:.2f}"}))
    st.dataframe(sty, width="stretch", height=580, hide_index=True)
    if "delisted" in sub.columns and sub["delisted"].any():
        st.caption(f"⚠ 含 {int(sub['delisted'].sum())} 只停牌/退市标的，前向收益用最后可得价。")
    st.caption("仅供研究参考，不构成投资建议。")


PAGES = {
    "🛰 驾驶舱": page_cockpit, "大盘": page_market, "决策": page_decision,
    "推荐跟踪": page_track, "模拟盘": page_paper, "网格": page_grid, "个股": page_stock,
    "选股": page_select, "资金流": page_fund_flow, "板块": page_sectors,
    "概览": page_overview,
}


def _header():
    r = _regime()
    state = r.get("state", "—")
    pos = r.get("suggested_position", "")
    badge = f'<span class="regime-pill cn">大盘 · {state} · {pos}</span>' if r else ""
    day = ""
    if store.has_table("daily_bar"):
        day = store.query("SELECT max(date) d FROM daily_bar")["d"].iloc[0]
    st.markdown(f"""
    <style>
    .aq-top{{display:flex;align-items:center;gap:14px;padding:4px 2px 14px;border-bottom:1px solid #1d2940;margin-bottom:16px}}
    .aq-top .lg{{font-size:1.35rem;font-weight:800;color:#fff;letter-spacing:1px}}
    .aq-top .lg i{{color:#f4b740;font-style:normal}}
    .aq-top .sub{{font-family:'PingFang SC';font-size:.72rem;color:#8595ad;letter-spacing:2px}}
    .aq-top .meta{{margin-left:auto;font-size:.74rem;color:#8595ad;display:flex;gap:16px;align-items:center}}
    .regime-pill{{font-size:.78rem;font-weight:600;padding:5px 13px;border-radius:3px;background:#3a2e12;color:#f4b740;border:1px solid #5e4a17}}
    </style>
    <div class="aq-top">
      <span class="lg">a<i>quant</i></span><span class="sub">量化投研驾驶舱</span>
      <span class="meta"><span>{day}　收盘</span>{badge}</span>
    </div>
    """, unsafe_allow_html=True)


def main():
    theme.inject()
    _header()
    choice = st.sidebar.radio("导航", list(PAGES))
    st.sidebar.caption("仅供研究，不构成投资建议")
    PAGES[choice]()


main()
