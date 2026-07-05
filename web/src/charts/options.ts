import type { Bar, SectorRow } from "../api/types";

export function buildKlineOption(bars: Bar[]): object {
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "category", data: bars.map((b) => b.date), scale: true },
    yAxis: { type: "value", scale: true },
    dataZoom: [{ type: "inside" }, { type: "slider" }],
    series: [
      {
        type: "candlestick",
        data: bars.map((b) => [b.open, b.close, b.low, b.high]),
        itemStyle: { color: "#ef4444", color0: "#22c55e", borderColor: "#ef4444", borderColor0: "#22c55e" },
      },
    ],
  };
}

export function buildSectorTreemapOption(rows: SectorRow[]): object {
  return {
    tooltip: { formatter: (p: { name: string; value: number }) => `${p.name}` },
    series: [
      {
        type: "treemap",
        roam: false,
        breadcrumb: { show: false },
        data: rows.map((r) => ({
          name: r.sector,
          value: r.mkt_cap ?? Math.abs(r.pct_chg),
          itemStyle: { color: r.pct_chg >= 0 ? "#ef4444" : "#22c55e" },
        })),
      },
    ],
  };
}

export function buildIndexBarOption(breadth: Record<string, number>): object {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 80, right: 20, top: 10, bottom: 20 },
    xAxis: { type: "value", max: 100 },
    yAxis: { type: "category", data: ["站上MA20%", "站上MA60%"] },
    series: [{ type: "bar", data: [breadth.above_ma20_pct ?? 0, breadth.above_ma60_pct ?? 0] }],
  };
}

export function buildNavLineOption(nav: { date: string; equity: number; benchmark: number | null }[]): object {
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["策略", "沪深300"], top: 0 },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: nav.map((p) => p.date) },
    yAxis: { type: "value", scale: true },
    dataZoom: [{ type: "inside" }, { type: "slider" }],
    series: [
      { name: "策略", type: "line", showSymbol: false, data: nav.map((p) => p.equity), itemStyle: { color: "#ef4444" } },
      { name: "沪深300", type: "line", showSymbol: false, data: nav.map((p) => p.benchmark), itemStyle: { color: "#9ca3af" } },
    ],
  };
}

export function buildFactorIcBarOption(rows: { factor: string; ir: number }[]): object {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 110, right: 20, top: 10, bottom: 30 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: rows.map((r) => r.factor) },
    series: [{
      type: "bar",
      data: rows.map((r) => ({ value: r.ir, itemStyle: { color: r.ir >= 0 ? "#ef4444" : "#22c55e" } })),
    }],
  };
}

export function buildMarketFundOption(series: { date: string; net: number }[]): object {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 50, right: 20, top: 10, bottom: 40 },
    xAxis: { type: "category", data: series.map((p) => p.date) },
    yAxis: { type: "value", name: "亿元" },
    series: [{
      type: "bar",
      data: series.map((p) => ({ value: p.net, itemStyle: { color: p.net >= 0 ? "#ef4444" : "#22c55e" } })),
    }],
  };
}

export function buildSectorFundTreemapOption(rows: { sector: string; main_net: number }[]): object {
  return {
    tooltip: {},
    series: [{
      type: "treemap", roam: false, breadcrumb: { show: false },
      data: rows.map((r) => ({
        name: r.sector, value: Math.abs(r.main_net),
        itemStyle: { color: r.main_net >= 0 ? "#ef4444" : "#22c55e" },
      })),
    }],
  };
}

export function buildSparklineOption(kline: { date: string; close: number }[]): object {
  const closes = kline.map((k) => k.close);
  const up = closes.length > 1 ? closes[closes.length - 1] >= closes[0] : true;
  return {
    grid: { left: 0, right: 0, top: 4, bottom: 4 },
    xAxis: { type: "category", show: false, data: kline.map((k) => k.date) },
    yAxis: { type: "value", show: false, scale: true },
    series: [{ type: "line", showSymbol: false, data: closes, lineStyle: { color: up ? "#ef4444" : "#22c55e", width: 1.5 }, areaStyle: { opacity: 0.08, color: up ? "#ef4444" : "#22c55e" } }],
  };
}

export function buildIndexTrendOption(points: { date: string; close: number; ma20: number | null; ma60: number | null }[]): object {
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["收盘", "MA20", "MA60"], top: 0, textStyle: { color: "#94a3b8" } },
    grid: { left: 50, right: 16, top: 28, bottom: 40 },
    xAxis: { type: "category", data: points.map((p) => p.date) },
    yAxis: { type: "value", scale: true },
    dataZoom: [{ type: "inside" }, { type: "slider" }],
    series: [
      { name: "收盘", type: "line", showSymbol: false, data: points.map((p) => p.close), lineStyle: { color: "#e5e7eb", width: 1.5 } },
      { name: "MA20", type: "line", showSymbol: false, data: points.map((p) => p.ma20), lineStyle: { color: "#f59e0b", width: 1 } },
      { name: "MA60", type: "line", showSymbol: false, data: points.map((p) => p.ma60), lineStyle: { color: "#38bdf8", width: 1 } },
    ],
  };
}

export function buildAmountBarOption(series: { date: string; amount: number }[]): object {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 50, right: 16, top: 10, bottom: 30 },
    xAxis: { type: "category", data: series.map((s) => s.date) },
    yAxis: { type: "value", name: "亿元" },
    series: [{
      type: "bar",
      data: series.map((s, i) => ({
        value: s.amount,
        itemStyle: { color: i > 0 && s.amount >= series[i - 1].amount ? "#ef4444" : "#64748b" },
      })),
    }],
  };
}

export function buildBreadthBarOption(up: number, down: number): object {
  return {
    grid: { left: 60, right: 16, top: 6, bottom: 20 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: ["上涨", "下跌"] },
    series: [{
      type: "bar",
      data: [{ value: up, itemStyle: { color: "#ef4444" } }, { value: down, itemStyle: { color: "#22c55e" } }],
    }],
  };
}
