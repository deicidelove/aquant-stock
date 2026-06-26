import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useSubmitFactorIc: () => ({ mutate: vi.fn() }),
  useFactorIcJob: () => ({ data: { status: "done", result: { rows: [{ factor: "volatility_20", ic_mean: 0.02, ic_std: 0.1, ir: 0.47, ic_win: 0.6, n: 100 }], fwd: 5 } } }),
}));
import QuantFactors from "./QuantFactors";

describe("QuantFactors", () => {
  it("renders run button and factor panel when done", () => {
    render(<QuantFactors />);
    expect(screen.getByRole("button", { name: /跑因子/ })).toBeInTheDocument();
    expect(screen.getByText("volatility_20")).toBeInTheDocument();
  });
});
