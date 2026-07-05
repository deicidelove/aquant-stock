import { describe, it, expect } from "vitest";
import { buildMarketFundOption, buildSectorFundTreemapOption } from "./options";

describe("macro chart options", () => {
  it("buildMarketFundOption maps dates + net bars", () => {
    const opt = buildMarketFundOption([{ date: "2026-06-22", net: -1.2 }, { date: "2026-06-23", net: 3.4 }]) as any;
    expect(opt.xAxis.data).toEqual(["2026-06-22", "2026-06-23"]);
    expect(opt.series[0].type).toBe("bar");
    expect(opt.series[0].data[1].value).toBe(3.4);
  });
  it("buildSectorFundTreemapOption maps sectors sized by abs(net)", () => {
    const opt = buildSectorFundTreemapOption([{ sector: "医药", main_net: 5e8 }, { sector: "煤炭", main_net: -2e8 }]) as any;
    expect(opt.series[0].type).toBe("treemap");
    expect(opt.series[0].data[0].name).toBe("医药");
    expect(opt.series[0].data[0].value).toBe(5e8);
  });
});
