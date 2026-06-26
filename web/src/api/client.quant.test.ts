import { describe, it, expect, vi, afterEach } from "vitest";
import { getQuantWeights, submitBacktest, getBacktestJob } from "./client";

afterEach(() => vi.restoreAllMocks());
function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok, status, json: async () => body } as Response);
}

describe("quant client", () => {
  it("getQuantWeights GETs presets", async () => {
    const f = mockFetch({ ic: { mom_20: 1 }, momentum: { mom_20: 1 } });
    await getQuantWeights();
    expect(f).toHaveBeenCalledWith("/api/quant/weights");
  });
  it("submitBacktest POSTs params", async () => {
    const f = mockFetch({ job_id: "abc" });
    const r = await submitBacktest({ capital: 1e6, weights: "ic", top_n: 5, rebalance_every: 5, min_history: 250 });
    expect(r.job_id).toBe("abc");
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/quant/backtest");
    expect(opts.method).toBe("POST");
  });
  it("getBacktestJob GETs by id", async () => {
    const f = mockFetch({ job_id: "abc", kind: "backtest", status: "done", result: { nav: [], metrics: {} }, error: null });
    await getBacktestJob("abc");
    expect(f).toHaveBeenCalledWith("/api/quant/backtest/abc");
  });
});
