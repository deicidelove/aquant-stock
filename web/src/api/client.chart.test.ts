import { describe, it, expect, vi, afterEach } from "vitest";
import { getStockChart } from "./client";
afterEach(() => vi.restoreAllMocks());

describe("chart client", () => {
  it("getStockChart hits chart path with n", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => ({ code: "600000", bars: [], ma: {}, macd: {} }) } as Response);
    await getStockChart("600000", 120);
    expect(f).toHaveBeenCalledWith("/api/stock/600000/chart?n=120");
  });
});
