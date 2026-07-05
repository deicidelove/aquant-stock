import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const { addWatch } = vi.hoisted(() => ({
  addWatch: vi.fn(async () => ({ codes: ["600000"] })),
}));

vi.mock("../api/client", () => ({
  getBoard: vi.fn(async () => ({ rows: [{ code: "600000", name: "浦发", last_price: 10, pct_chg: 1, kline: [], signal: "买入/增持", one_liner: "x", battle_plan: {}, risk_level: "低", alerts: [] }] })),
  addWatch,
}));
import { useBoard, useAddWatch } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("board hooks", () => {
  it("useBoard returns rows", async () => {
    const { result } = renderHook(() => useBoard(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].code).toBe("600000");
  });
  it("useAddWatch mutation calls client.addWatch", async () => {
    const { result } = renderHook(() => useAddWatch(), { wrapper });
    await act(async () => { await result.current.mutateAsync("600000"); });
    expect(addWatch).toHaveBeenCalled();
    expect(addWatch.mock.calls[0][0]).toBe("600000");
  });
});
