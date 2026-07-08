import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import BlockTradePanel from "./BlockTradePanel";

describe("BlockTradePanel", () => {
  it("renders rows with amount + premium", () => {
    render(<BlockTradePanel data={{ rows: [
      { date: "2026-07-07", total_amount: 26.2, premium_ratio: 0.4 },
    ] }} />);
    expect(screen.getByText("26.2 亿")).toBeInTheDocument();
    expect(screen.getByText(/溢价 40%/)).toBeInTheDocument();
  });

  it("empty hint", () => {
    render(<BlockTradePanel data={{ rows: [] }} />);
    expect(screen.getByText(/暂无大宗交易/)).toBeInTheDocument();
  });
});
