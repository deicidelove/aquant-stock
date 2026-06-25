import { describe, it, expect } from "vitest";
import { buildNavLineOption, buildFactorIcBarOption } from "./options";

describe("quant chart options", () => {
  it("buildNavLineOption maps two series over dates", () => {
    const nav = [
      { date: "2026-06-01", equity: 1.0, benchmark: 1.0 },
      { date: "2026-06-02", equity: 1.05, benchmark: 1.02 },
    ];
    const opt = buildNavLineOption(nav) as any;
    expect(opt.xAxis.data).toEqual(["2026-06-01", "2026-06-02"]);
    expect(opt.series).toHaveLength(2);
    expect(opt.series[0].data).toEqual([1.0, 1.05]);
    expect(opt.series[1].data).toEqual([1.0, 1.02]);
  });
  it("buildFactorIcBarOption maps factor IR bars", () => {
    const opt = buildFactorIcBarOption([{ factor: "volatility_20", ir: 0.47 }, { factor: "mom_20", ir: -0.41 }]) as any;
    expect(opt.series[0].type).toBe("bar");
    expect(opt.yAxis.data).toEqual(["volatility_20", "mom_20"]);
    expect(opt.series[0].data[0].value).toBe(0.47);
  });
});
