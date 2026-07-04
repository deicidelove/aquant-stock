import { describe, it, expect, vi, afterEach } from "vitest";
import { getSentimentMacro, getMarketFund, getAbnormal } from "./client";

afterEach(() => vi.restoreAllMocks());
function mockFetch(body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => body } as Response);
}

describe("macro client", () => {
  it("getSentimentMacro GETs /api/cockpit/sentiment", async () => {
    const f = mockFetch({ up: 1, down: 2, limit_up: 0, limit_down: 0, amount: 0, score: 50, label: "中性" });
    await getSentimentMacro();
    expect(f).toHaveBeenCalledWith("/api/cockpit/sentiment");
  });
  it("getMarketFund passes days", async () => {
    const f = mockFetch({ today: 1, series: [] });
    await getMarketFund(5);
    expect(f).toHaveBeenCalledWith("/api/cockpit/market-fund?days=5");
  });
  it("getAbnormal passes scope/n/z", async () => {
    const f = mockFetch({ scope: "sector", rows: [] });
    await getAbnormal("sector", 10, 2.5);
    expect(f).toHaveBeenCalledWith("/api/cockpit/abnormal?scope=sector&n=10&z=2.5");
  });
});
