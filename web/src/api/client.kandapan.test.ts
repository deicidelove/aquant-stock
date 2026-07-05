import { describe, it, expect, vi, afterEach } from "vitest";
import { getRegime, getIndexSeries, getAmountTrend } from "./client";

afterEach(() => vi.restoreAllMocks());
function mockFetch(body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => body } as Response);
}

describe("kandapan client", () => {
  it("getRegime GETs /api/cockpit/regime", async () => {
    const f = mockFetch({ state: "防守", score: 1 });
    await getRegime();
    expect(f).toHaveBeenCalledWith("/api/cockpit/regime");
  });
  it("getIndexSeries passes code+n", async () => {
    const f = mockFetch({ code: "sh000300", points: [] });
    await getIndexSeries("sh000300", 60);
    expect(f).toHaveBeenCalledWith("/api/cockpit/index-series?code=sh000300&n=60");
  });
  it("getAmountTrend passes days", async () => {
    const f = mockFetch({ series: [] });
    await getAmountTrend(5);
    expect(f).toHaveBeenCalledWith("/api/cockpit/amount-trend?days=5");
  });
});
