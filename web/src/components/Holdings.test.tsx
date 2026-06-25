import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import HoldingsPanel from "./HoldingsPanel";
import PnlSummary from "./PnlSummary";

const rows = [
  { code: "600000", name: "浦发", shares: 1000, avg_cost: 11, last_price: 13.95, market_value: 13950, unrealized: 2950, unrealized_pct: 26.8, alerts: ["跌破止损"] },
];

describe("HoldingsPanel / PnlSummary", () => {
  it("renders holding row and fires onPick", () => {
    const onPick = vi.fn();
    render(<HoldingsPanel rows={rows} onPick={onPick} />);
    expect(screen.getByText("浦发")).toBeInTheDocument();
    expect(screen.getByText("跌破止损")).toBeInTheDocument();
    fireEvent.click(screen.getByText("浦发"));
    expect(onPick).toHaveBeenCalledWith("600000");
  });
  it("PnlSummary shows totals", () => {
    render(<PnlSummary pnl={{ realized: 1000, unrealized: 2950, total: 3950 }} />);
    expect(screen.getByText(/3950/)).toBeInTheDocument();
  });
});
