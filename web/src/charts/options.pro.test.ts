import { describe, it, expect } from "vitest";
import { buildProKlineOption } from "./options";

const chart = {
  code: "600000",
  bars: [
    { date: "d1", open: 10, high: 11, low: 9, close: 10.5, volume: 100 },
    { date: "d2", open: 10.5, high: 12, low: 10, close: 11, volume: 120 },
  ],
  ma: { ma5: [null, 10.7], ma10: [null, null], ma20: [null, null], ma60: [null, null] },
  macd: { dif: [0.1, 0.2], dea: [0.05, 0.1], hist: [0.1, 0.2] },
};

describe("buildProKlineOption", () => {
  it("has 3 grids/xAxis and candlestick+4MA+vol+macd series", () => {
    const opt = buildProKlineOption(chart as any) as any;
    expect(opt.grid).toHaveLength(3);
    expect(opt.xAxis).toHaveLength(3);
    const types = opt.series.map((s: any) => s.type);
    expect(types.filter((t: string) => t === "candlestick")).toHaveLength(1);
    expect(types.filter((t: string) => t === "line")).toHaveLength(6);
    expect(types.filter((t: string) => t === "bar")).toHaveLength(2);
    const k = opt.series.find((s: any) => s.type === "candlestick");
    expect(k.data[0]).toEqual([10, 10.5, 9, 11]);
  });
  it("adds markLine when plan given", () => {
    const opt = buildProKlineOption(chart as any, { stop_loss: 9.5, take_profit: 12 }) as any;
    const k = opt.series.find((s: any) => s.type === "candlestick");
    expect(k.markLine).toBeTruthy();
    expect(k.markLine.data).toHaveLength(2);
  });
});
