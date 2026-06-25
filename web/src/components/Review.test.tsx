import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BriefingPanel from "./BriefingPanel";
import ScorecardPanel from "./ScorecardPanel";

describe("BriefingPanel / ScorecardPanel", () => {
  it("BriefingPanel renders row and fires onPick", () => {
    const onPick = vi.fn();
    render(<BriefingPanel rows={[{ code: "600000", name: "浦发", 综合分: 1.2, 信号: "买入/增持", 买点: 10.1, 止损: 9.5, 目标: 12 }]} onPick={onPick} />);
    fireEvent.click(screen.getByText("浦发"));
    expect(onPick).toHaveBeenCalledWith("600000");
  });
  it("ScorecardPanel renders rows or empty hint", () => {
    render(<ScorecardPanel data={{ as_of: "2026-06-01", rows: [{ as_of: "2026-06-01", code: "600000", rank: 1, exc_20: 0.01 }] }} />);
    expect(screen.getByText("600000")).toBeInTheDocument();
    render(<ScorecardPanel data={{ as_of: null, rows: [] }} />);
    expect(screen.getByText(/暂无/)).toBeInTheDocument();
  });
});
