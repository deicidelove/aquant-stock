import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("../api/client", () => ({
  getQuantWeights: vi.fn(async () => ({ ic: { mom_20: 1 }, momentum: { mom_20: 1 } })),
  getBacktestJob: vi.fn(async () => ({ job_id: "abc", kind: "backtest", status: "done", result: { nav: [], metrics: { sharpe: 1 }, top_n: 5, rebalance_every: 5 }, error: null })),
}));
import { useQuantWeights, useBacktestJob } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("quant hooks", () => {
  it("useQuantWeights returns presets", async () => {
    const { result } = renderHook(() => useQuantWeights(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.ic.mom_20).toBe(1);
  });
  it("useBacktestJob polls when jobId set and returns done", async () => {
    const { result } = renderHook(() => useBacktestJob("abc"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.status).toBe("done");
  });
  it("useBacktestJob disabled when jobId null", () => {
    const { result } = renderHook(() => useBacktestJob(null), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });
});
