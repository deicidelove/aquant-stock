import { describe, it, expect } from "vitest";
import { buildSparklineOption } from "./options";
describe("sparkline option", () => {
  it("maps closes to a line series, up=red", () => {
    const opt = buildSparklineOption([{ date: "d1", close: 10 }, { date: "d2", close: 11 }]) as any;
    expect(opt.series[0].type).toBe("line");
    expect(opt.series[0].data).toEqual([10, 11]);
    expect(opt.series[0].lineStyle.color).toBe("#ef4444"); // 涨=红
  });
});
