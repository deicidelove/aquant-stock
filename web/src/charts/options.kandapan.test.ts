import { describe, it, expect } from "vitest";
import { buildIndexTrendOption, buildAmountBarOption, buildBreadthBarOption } from "./options";

describe("kandapan options", () => {
  it("index trend has 3 series over dates", () => {
    const opt = buildIndexTrendOption([{ date: "d1", close: 3900, ma20: 3890, ma60: 3850 }]) as any;
    expect(opt.xAxis.data).toEqual(["d1"]);
    expect(opt.series).toHaveLength(3);
    expect(opt.series[0].data).toEqual([3900]);
  });
  it("amount bar maps amounts", () => {
    const opt = buildAmountBarOption([{ date: "d1", amount: 9000 }, { date: "d2", amount: 9500 }]) as any;
    expect(opt.series[0].type).toBe("bar");
    expect(opt.series[0].data[1].value).toBe(9500);
  });
  it("breadth bar shows up/down", () => {
    const opt = buildBreadthBarOption(3000, 1800) as any;
    expect(opt.series[0].type).toBe("bar");
    expect(opt.series[0].data[0].value).toBe(3000);
    expect(opt.series[0].data[1].value).toBe(1800);
  });
});
