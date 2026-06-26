import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import FactorIcPanel from "./FactorIcPanel";

describe("FactorIcPanel", () => {
  it("renders chart and factor rows", () => {
    render(<FactorIcPanel rows={[{ factor: "volatility_20", ic_mean: 0.02, ic_std: 0.1, ir: 0.47, ic_win: 0.6, n: 100 }]} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
    expect(screen.getByText("volatility_20")).toBeInTheDocument();
  });
  it("shows empty hint when no rows", () => {
    render(<FactorIcPanel rows={[]} />);
    expect(screen.getByText(/暂无/)).toBeInTheDocument();
  });
});
