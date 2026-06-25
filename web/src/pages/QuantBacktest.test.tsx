import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useQuantWeights: () => ({ isSuccess: true, data: { ic: { mom_20: 1 }, momentum: { mom_20: 1 } } }),
  useSubmitBacktest: () => ({ mutate: vi.fn() }),
  useBacktestJob: () => ({ data: { status: "done", result: { nav: [{ date: "2026-06-01", equity: 1, benchmark: 1 }], metrics: { sharpe: 1.4 }, top_n: 5, rebalance_every: 5 } } }),
}));
import QuantBacktest from "./QuantBacktest";

describe("QuantBacktest", () => {
  it("renders form + result when job done", () => {
    render(<QuantBacktest />);
    expect(screen.getByText("回测配置")).toBeInTheDocument();
    expect(screen.getByText("绩效")).toBeInTheDocument();
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});
