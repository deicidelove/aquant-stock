import { describe, it, expect } from "vitest";
import { buildKlineOption, buildSectorTreemapOption } from "./options";

describe("chart options", () => {
  it("buildKlineOption maps bars to candlestick series + date axis", () => {
    const bars = [
      { date: "2026-06-22", open: 10, high: 11, low: 9, close: 10.5, volume: 100 },
      { date: "2026-06-23", open: 10.5, high: 12, low: 10, close: 11.8, volume: 120 },
    ];
    const opt = buildKlineOption(bars) as any;
    expect(opt.xAxis.data).toEqual(["2026-06-22", "2026-06-23"]);
    expect(opt.series[0].type).toBe("candlestick");
    // ECharts 蜡烛序列数据顺序为 [open, close, low, high]
    expect(opt.series[0].data[0]).toEqual([10, 10.5, 9, 11]);
  });

  it("buildSectorTreemapOption maps sectors to sized/colored nodes", () => {
    const rows = [{ sector: "银行", pct_chg: 1.5, mkt_cap: 5e11 }, { sector: "煤炭", pct_chg: -0.8, mkt_cap: 2e11 }];
    const opt = buildSectorTreemapOption(rows) as any;
    expect(opt.series[0].type).toBe("treemap");
    expect(opt.series[0].data[0].name).toBe("银行");
    expect(opt.series[0].data[0].value).toBe(5e11);
  });
});
