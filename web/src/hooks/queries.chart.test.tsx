import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
vi.mock("../api/client", () => ({
  getStockChart: vi.fn(async () => ({ code: "600000", bars: [{ date: "d", open: 1, high: 2, low: 0.5, close: 1.5, volume: 100 }], ma: { ma5: [null] }, macd: { dif: [0.1], dea: [0.05], hist: [0.1] } })),
}));
import { useStockChart } from "./queries";
function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
describe("useStockChart", () => {
  it("returns chart data", async () => {
    const { result } = renderHook(() => useStockChart("600000"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.bars[0].close).toBe(1.5);
  });
  it("disabled when code empty", () => {
    const { result } = renderHook(() => useStockChart(""), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });
});
