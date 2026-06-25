import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("../api/client", () => ({
  getOverview: vi.fn(async () => ({ breadth: { up: 10 }, regime: { state: "进攻", score: 4 }, index: { code: "sh000300", close: 3900 } })),
  getTopScores: vi.fn(async () => ({ as_of: "2026-06-23", rows: [{ code: "600000", name: "浦发", score: 1.2 }] })),
}));

import { useOverview, useTopScores } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("query hooks", () => {
  it("useOverview returns mapped data", async () => {
    const { result } = renderHook(() => useOverview(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.regime.state).toBe("进攻");
  });
  it("useTopScores passes top and returns rows", async () => {
    const { result } = renderHook(() => useTopScores(5), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].code).toBe("600000");
  });
});
