import { describe, it, expect, vi, afterEach } from "vitest";
import { getOverview, getKline } from "./client";

afterEach(() => vi.restoreAllMocks());

function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok, status, json: async () => body,
  } as Response);
}

describe("api client", () => {
  it("getOverview hits /api/cockpit/overview and returns json", async () => {
    const f = mockFetch({ breadth: { up: 2500 }, regime: { state: "均衡" }, index: { close: 3900 } });
    const r = await getOverview();
    expect(f).toHaveBeenCalledWith("/api/cockpit/overview");
    expect(r.regime.state).toBe("均衡");
  });

  it("getKline passes code and n in the path", async () => {
    const f = mockFetch({ code: "600000", bars: [] });
    await getKline("600000", 120);
    expect(f).toHaveBeenCalledWith("/api/stock/600000/kline?n=120");
  });

  it("throws on non-2xx", async () => {
    mockFetch({}, false, 404);
    await expect(getKline("xxxxxx")).rejects.toThrow();
  });
});
