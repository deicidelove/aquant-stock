import { describe, it, expect, vi, afterEach } from "vitest";
import { getHoldings, addTrade, deleteTrade, getBriefing } from "./client";

afterEach(() => vi.restoreAllMocks());

function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok, status, json: async () => body } as Response);
}

describe("assist/holdings client", () => {
  it("getHoldings GETs /api/holdings", async () => {
    const f = mockFetch({ rows: [] });
    await getHoldings();
    expect(f).toHaveBeenCalledWith("/api/holdings");
  });
  it("addTrade POSTs with JSON body", async () => {
    const f = mockFetch({ tid: 1 });
    const r = await addTrade({ date: "2026-02-02", code: "600000", side: "buy", shares: 100, price: 10 });
    expect(r.tid).toBe(1);
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/holdings/trade");
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body as string).code).toBe("600000");
  });
  it("deleteTrade DELETEs by tid", async () => {
    const f = mockFetch({ deleted: 1 });
    await deleteTrade(3);
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/holdings/trade/3");
    expect(opts.method).toBe("DELETE");
  });
  it("getBriefing passes top", async () => {
    const f = mockFetch({ rows: [] });
    await getBriefing(5);
    expect(f).toHaveBeenCalledWith("/api/assist/briefing?top=5");
  });
});
