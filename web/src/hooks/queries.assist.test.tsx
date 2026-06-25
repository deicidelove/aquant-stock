import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const { addTrade } = vi.hoisted(() => ({ addTrade: vi.fn(async () => ({ tid: 1 })) }));
vi.mock("../api/client", () => ({
  getHoldings: vi.fn(async () => ({ rows: [{ code: "600000", name: "浦发", shares: 100, avg_cost: 10, last_price: 11, market_value: 1100, unrealized: 100, unrealized_pct: 10, alerts: [] }] })),
  getPnl: vi.fn(async () => ({ realized: 0, unrealized: 100, total: 100 })),
  addTrade,
}));

import { useHoldings, usePnl, useAddTrade } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("assist hooks", () => {
  it("useHoldings returns rows", async () => {
    const { result } = renderHook(() => useHoldings(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].code).toBe("600000");
  });
  it("usePnl returns totals", async () => {
    const { result } = renderHook(() => usePnl(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.total).toBe(100);
  });
  it("useAddTrade mutation calls client.addTrade", async () => {
    const { result } = renderHook(() => useAddTrade(), { wrapper });
    await act(async () => { await result.current.mutateAsync({ date: "2026-02-02", code: "600000", side: "buy", shares: 100, price: 10 }); });
    expect(addTrade).toHaveBeenCalled();
  });
});
