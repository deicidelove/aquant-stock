"""看盘 UI 主题：深色 Bloomberg 风。注入全局 CSS + 主题化组件 + Plotly 深色模板。

一次 inject() 即覆盖所有页面；关键区块用 kpi_row/badge 等渲染主题化 HTML。
A股配色铁律：红涨绿跌（up=红 down=绿）。
"""
from __future__ import annotations

import streamlit as st

UP = "#ff3b47"
DOWN = "#19c39a"
AMBER = "#f4b740"
INK2 = "#8595ad"

# Plotly 深色模板（红涨绿跌）
PLOTLY_DARK = dict(
    paper_bgcolor="#0f1622", plot_bgcolor="#0f1622",
    font=dict(color="#cdd9ea", family="JetBrains Mono, monospace", size=12),
    colorway=[AMBER, "#3fa7ff", UP, DOWN, "#b07cff"],
    xaxis=dict(gridcolor="#1d2940", zerolinecolor="#1d2940"),
    yaxis=dict(gridcolor="#1d2940", zerolinecolor="#1d2940"),
    margin=dict(t=40, l=10, r=10, b=10),
)
# 红涨绿跌的连续色阶（用于 treemap/heatmap）
RG_SCALE = [DOWN, "#1b2433", UP]


def style_fig(fig):
    """给 plotly 图套深色模板。"""
    fig.update_layout(**PLOTLY_DARK)
    return fig


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');
:root{--up:#ff3b47;--down:#19c39a;--amber:#f4b740;--line:#1d2940;--panel:#0f1622;--ink:#cdd9ea;--ink2:#8595ad}
html,body,[class*="css"]{font-family:'JetBrains Mono',ui-monospace,Menlo,monospace}
/* 背景网格纹理 */
.stApp{
  background:
    linear-gradient(rgba(29,41,64,.18) 1px,transparent 1px),
    linear-gradient(90deg,rgba(29,41,64,.18) 1px,transparent 1px),
    radial-gradient(120% 100% at 85% -10%,rgba(63,167,255,.08),transparent 55%),
    #070a0f;
  background-size:46px 46px,46px 46px,100% 100%,100% 100%;
}
/* 隐藏默认 chrome */
#MainMenu,header[data-testid="stHeader"],footer{display:none!important}
.block-container{padding-top:1.4rem;padding-bottom:2rem;max-width:1340px}
/* 标题 */
h1,h2,h3,h4{font-family:'PingFang SC','Microsoft YaHei',sans-serif!important;letter-spacing:.5px}
h1{font-size:1.5rem!important;color:#fff!important}
h2{font-size:1.15rem!important} h3{font-size:.95rem!important;color:var(--ink)!important}
/* 侧边栏 */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0f18,#070a0f);border-right:1px solid var(--line)}
[data-testid="stSidebar"] *{font-family:'PingFang SC',sans-serif}
[data-testid="stSidebar"] label{letter-spacing:1px}
/* 单选导航 */
[data-testid="stSidebar"] [role="radiogroup"] label{padding:6px 10px;border-radius:4px;transition:.15s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#101a2b}
/* 指标卡（原生 st.metric 兜底美化）*/
[data-testid="stMetric"]{background:linear-gradient(180deg,#0f1622,#0c111a);border:1px solid var(--line);
  border-radius:6px;padding:12px 14px}
[data-testid="stMetricValue"]{font-size:1.35rem!important;font-variant-numeric:tabular-nums}
[data-testid="stMetricLabel"]{color:var(--ink2)!important}
/* 表格 */
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:6px}
/* 按钮 */
.stButton button{background:var(--amber)!important;color:#1a1205!important;border:none!important;
  font-family:'PingFang SC',sans-serif;font-weight:600;border-radius:4px}
.stButton button:hover{filter:brightness(1.08)}
/* 滑块 / 选择框标签 */
.stSlider label,.stSelectbox label,.stCheckbox label,.stRadio label{font-family:'PingFang SC',sans-serif;color:var(--ink2)!important}
hr{border-color:var(--line)!important}
/* 自定义组件 */
.aq-panel{background:linear-gradient(180deg,#0f1622,#0c111a);border:1px solid var(--line);border-radius:6px;padding:14px 16px;margin-bottom:12px}
.aq-ph{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.aq-ph .bar{width:3px;height:13px;background:var(--amber);border-radius:2px}
.aq-ph h3{font-family:'PingFang SC',sans-serif;font-size:.85rem;font-weight:600;margin:0}
.aq-kpis{display:flex;gap:10px;flex-wrap:wrap}
.aq-kpi{flex:1;min-width:110px;background:linear-gradient(180deg,#0f1622,#0c111a);border:1px solid var(--line);
  border-radius:6px;padding:11px 13px}
.aq-kpi .k{font-size:.64rem;color:var(--ink2);font-family:'PingFang SC',sans-serif}
.aq-kpi .v{font-size:1.3rem;font-weight:800;font-variant-numeric:tabular-nums;margin-top:3px;line-height:1.1}
.aq-kpi .v small{font-size:.6rem;color:var(--ink2);font-weight:400}
.aq-up{color:var(--up)!important} .aq-down{color:var(--down)!important} .aq-amber{color:var(--amber)!important}
/* 主题化表格 */
.aq-table{width:100%;border-collapse:collapse;font-family:'JetBrains Mono',monospace;font-size:.82rem}
.aq-table th{font-family:'PingFang SC',sans-serif;font-size:.66rem;color:#566077;text-align:right;
  padding:8px 10px;border-bottom:1px solid #2a3a59;white-space:nowrap}
.aq-table th:first-child,.aq-table th:nth-child(2){text-align:left}
.aq-table td{padding:10px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap;font-variant-numeric:tabular-nums}
.aq-table td:first-child,.aq-table td:nth-child(2){text-align:left}
.aq-table tr:hover td{background:#101a2b}
.aq-code{color:var(--ink2);font-size:.74rem}
.aq-name{font-family:'PingFang SC',sans-serif;color:#fff;font-weight:600}
.aq-badge{font-family:'PingFang SC',sans-serif;font-size:.68rem;font-weight:600;padding:3px 9px;border-radius:3px}
.b-buy{background:#5a1f25;color:#ff7a82;border:1px solid #6e2a30}
.b-hold{background:#3a2e12;color:var(--amber);border:1px solid #5e4a17}
.b-avoid{background:#103f37;color:#4fe0bd;border:1px solid #1c5a4d}
.r-low{color:var(--down)} .r-mid{color:var(--amber)} .r-high{color:var(--up)}
/* 名称悬浮 K 线弹层 */
.aq-knm{position:relative;cursor:pointer;border-bottom:1px dashed #46577a}
.aq-kpop{display:none;position:absolute;left:0;top:135%;z-index:999;padding:5px;
  background:#0a0f18;border:1px solid #2a3a59;border-radius:6px;box-shadow:0 10px 34px rgba(0,0,0,.7)}
.aq-knm:hover .aq-kpop{display:block}
/* 利好/利空 多行展示（覆盖表格 nowrap）*/
.aq-news{white-space:normal!important;word-break:break-word;max-width:240px;
  font-family:'PingFang SC',sans-serif!important;font-size:.7rem;line-height:1.45;text-align:left!important}
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)


def panel_header(title: str, tag: str = ""):
    t = f'<span style="margin-left:auto;font-size:.62rem;color:#566077;letter-spacing:1px">{tag}</span>' if tag else ""
    st.markdown(f'<div class="aq-ph"><span class="bar"></span><h3>{title}</h3>{t}</div>',
                unsafe_allow_html=True)


def _cls(v):
    try:
        return "aq-up" if float(v) > 0 else "aq-down" if float(v) < 0 else ""
    except Exception:
        return ""


def kpi_row(items: list[dict]):
    """items: [{label, value, sub?, color?('up'/'down'/'amber'/auto)}]"""
    cells = []
    for it in items:
        c = it.get("color")
        cls = {"up": "aq-up", "down": "aq-down", "amber": "aq-amber"}.get(c, "")
        if c == "auto":
            cls = _cls(it.get("value"))
        sub = f'<small>{it["sub"]}</small>' if it.get("sub") else ""
        cells.append(f'<div class="aq-kpi"><div class="k">{it["label"]}</div>'
                     f'<div class="v {cls}">{it["value"]}{sub}</div></div>')
    st.markdown(f'<div class="aq-kpis">{"".join(cells)}</div>', unsafe_allow_html=True)
